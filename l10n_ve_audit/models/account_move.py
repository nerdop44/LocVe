# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        moves = super(AccountMove, self).create(vals_list)
        for move in moves:
            if move.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund', 'out_receipt', 'in_receipt']:
                # Registrar creación de factura en log de auditoría
                details = f"Creación de documento tipo '{move.move_type}' en estado Borrador."
                self.env['l10n_ve.audit.log'].log_event('create', move, details)
        return moves

    def action_post(self):
        res = super(AccountMove, self).write_vals_before_post_or_similar() if hasattr(self, 'write_vals_before_post_or_similar') else True
        # Llamar al super original
        post_result = super(AccountMove, self).action_post()
        for move in self:
            if move.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund', 'out_receipt', 'in_receipt']:
                # Registrar publicación / asentamiento fiscal
                details = (f"Documento asentado. Número fiscal asignado: {move.name}. "
                           f"Correlativo/Control: {move.correlative or 'No asignado'}. "
                           f"Cliente/Proveedor: {move.partner_id.name} (RIF: {move.partner_id.vat or 'S/R'}). "
                           f"Monto Total: {move.amount_total} Bs / {move.amount_total_usd if hasattr(move, 'amount_total_usd') else 0} USD.")
                
                if move.move_type == 'out_refund' and move.journal_id.l10n_ve_is_free_form:
                    details += f" [FORMA LIBRE NC]"
                    if move.reversed_entry_id:
                        details += (f" Factura Afectada: {move.reversed_entry_id.name} "
                                    f"(Control Afectado: {move.reversed_entry_id.correlative or 'Ninguno'}, "
                                    f"Fecha Afectada: {move.reversed_entry_id.invoice_date}). "
                                    f"Motivo Reversión: {move.ref or 'No especificado'}.")
                
                self.env['l10n_ve.audit.log'].log_event('post', move, details)
        return post_result

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for move in self:
            if move.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund', 'out_receipt', 'in_receipt']:
                details = f"Documento devuelto al estado Borrador. Nombre anterior: {move.name}. Control anterior: {move.correlative}."
                self.env['l10n_ve.audit.log'].log_event('draft', move, details)
        return res

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        for move in self:
            if move.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund', 'out_receipt', 'in_receipt']:
                details = f"Documento cancelado / anulado. Nombre: {move.name}. Control: {move.correlative}."
                self.env['l10n_ve.audit.log'].log_event('cancel', move, details)
        return res

    def unlink(self):
        # Capturar la información crítica antes de la destrucción del registro
        for move in self:
            if move.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund', 'out_receipt', 'in_receipt']:
                details = (f"ELIMINACIÓN DE REGISTRO. "
                           f"ID Registro: {move.id}. "
                           f"Último Nombre: {move.name or 'Borrador'}. "
                           f"Último Control: {move.correlative or 'Ninguno'}. "
                           f"Monto: {move.amount_total} Bs. "
                           f"Cliente/Proveedor: {move.partner_id.name or 'S/N'} (RIF: {move.partner_id.vat or 'S/R'}).")
                # Se crea un registro de log antes de la eliminación
                self.env['l10n_ve.audit.log'].log_event('unlink', move, details)
        return super(AccountMove, self).unlink()

    def _reverse_moves(self, default_values_list=None, cancel=False):
        # Odoo genera notas de crédito mediante _reverse_moves
        reversed_moves = super(AccountMove, self)._reverse_moves(default_values_list=default_values_list, cancel=cancel)
        for move, reversed_move in zip(self, reversed_moves):
            if move.move_type in ['out_invoice', 'in_invoice']:
                details = (f"Reversión generada (Nota de Crédito/Reembolso). "
                           f"Documento Origen: {move.name} (Control: {move.correlative}). "
                           f"Nota de Crédito Creada: {reversed_move.name or 'Borrador'}. "
                           f"Monto Revertido: {reversed_move.amount_total} Bs.")
                self.env['l10n_ve.audit.log'].log_event('reversal', reversed_move, details)
        return reversed_moves
