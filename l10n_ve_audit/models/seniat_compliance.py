# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(SaleOrderLine, self).create(vals_list)

    def write(self, vals):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(SaleOrderLine, self).write(vals)

    def unlink(self):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(SaleOrderLine, self).unlink()

    @api.constrains('price_unit')
    def _check_price_unit_positive(self):
        for line in self:
            if not line.display_type:
                if line.price_unit <= 0.0:
                    raise ValidationError(_("El precio unitario del producto '%s' debe ser mayor a cero.") % line.product_id.name)

    @api.constrains('tax_id')
    def _check_single_tax(self):
        for line in self:
            if not line.display_type and len(line.tax_id) > 1:
                raise ValidationError(_("No se permite aplicar más de una alícuota de impuesto al producto '%s'.") % line.product_id.name)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(PurchaseOrderLine, self).create(vals_list)

    def write(self, vals):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(PurchaseOrderLine, self).write(vals)

    def unlink(self):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(PurchaseOrderLine, self).unlink()

    @api.constrains('price_unit')
    def _check_price_unit_positive(self):
        for line in self:
            if not line.display_type:
                if line.price_unit <= 0.0:
                    raise ValidationError(_("El precio unitario del producto '%s' debe ser mayor a cero.") % line.product_id.name)

    @api.constrains('taxes_id')
    def _check_single_tax(self):
        for line in self:
            if not line.display_type and len(line.taxes_id) > 1:
                raise ValidationError(_("No se permite aplicar más de una alícuota de impuesto al producto '%s'.") % line.product_id.name)

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'correlative' in vals and vals['correlative']:
                vals['correlative'] = self._format_control_number(vals['correlative'])
        return super(AccountMove, self).create(vals_list)

    def write(self, vals):
        if 'correlative' in vals and vals['correlative']:
            vals['correlative'] = self._format_control_number(vals['correlative'])
        return super(AccountMove, self).write(vals)

    def _format_control_number(self, val):
        if not val:
            return val
        # Limpiar cualquier caracter que no sea dígito
        digits = ''.join(c for c in val if c.isdigit())
        if not digits:
            return val
        # Rellenar con ceros a la izquierda hasta 8 dígitos y anteponer '00-'
        return f"00-{digits[-8:].zfill(8)}"

    @api.constrains('reversed_entry_id', 'state')
    def _check_invoice_not_fully_refunded(self):
        for move in self:
            if move.move_type in ('out_refund', 'in_refund') and move.state == 'posted' and move.reversed_entry_id:
                invoice = move.reversed_entry_id
                # Buscar todas las notas de crédito publicadas para esta factura
                refunds = self.search([
                    ('reversed_entry_id', '=', invoice.id),
                    ('state', '=', 'posted'),
                    ('move_type', '=', move.move_type)
                ])
                total_refunded = sum(refunds.mapped('amount_total'))
                if total_refunded > invoice.amount_total + 0.01:
                    raise ValidationError(_("La factura '%s' ya ha sido totalmente afectada por otra(s) Nota(s) de Crédito. No es posible emitir reembolsos que excedan el monto total de la factura original.") % invoice.name)

    @api.constrains('invoice_line_ids', 'reversed_entry_id', 'state')
    def _check_credit_note_lines(self):
        for move in self:
            if move.move_type in ('out_refund', 'in_refund') and move.reversed_entry_id and move.state == 'posted':
                invoice = move.reversed_entry_id
                
                # Mapear cantidades facturadas por producto
                original_qty = {}
                for line in invoice.invoice_line_ids:
                    if not line.display_type and line.product_id:
                        original_qty[line.product_id.id] = original_qty.get(line.product_id.id, 0.0) + line.quantity
                
                # Buscar cantidades ya reembolsadas en notas de crédito publicadas
                other_refunds = self.search([
                    ('reversed_entry_id', '=', invoice.id),
                    ('state', '=', 'posted'),
                    ('move_type', '=', move.move_type)
                ])
                
                refund_qty = {}
                for r in other_refunds:
                    for line in r.invoice_line_ids:
                        if not line.display_type and line.product_id:
                            prod_id = line.product_id.id
                            refund_qty[prod_id] = refund_qty.get(prod_id, 0.0) + line.quantity
                
                # Validar cada línea de la nota de crédito actual
                for line in move.invoice_line_ids:
                    if not line.display_type and line.product_id:
                        prod_id = line.product_id.id
                        if prod_id not in original_qty:
                            raise ValidationError(_("No se permite agregar el producto '%s' a la Nota de Crédito, ya que no forma parte de la factura original.") % line.product_id.name)
                        
                        total_ref_qty = refund_qty.get(prod_id, 0.0)
                        if total_ref_qty > original_qty[prod_id] + 0.0001:
                            raise ValidationError(_("La cantidad total reembolsada del producto '%s' (%s) excede la cantidad facturada originalmente (%s).") % (
                                line.product_id.name, total_ref_qty, original_qty[prod_id]
                            ))

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(AccountMoveLine, self).create(vals_list)

    def write(self, vals):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(AccountMoveLine, self).write(vals)

    def unlink(self):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(AccountMoveLine, self).unlink()

    @api.constrains('price_unit')
    def _check_price_unit_positive(self):
        for line in self:
            if line.move_id.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt'):
                if not line.display_type:
                    # Solo validar líneas de productos reales
                    if line.product_id and line.price_unit <= 0.0:
                        raise ValidationError(_("El precio unitario de la línea de producto '%s' debe ser mayor a cero.") % line.name)

    @api.constrains('tax_ids')
    def _check_single_tax(self):
        for line in self:
            if line.move_id.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt'):
                if not line.display_type and line.product_id and len(line.tax_ids) > 1:
                    raise ValidationError(_("No se permite aplicar más de una alícuota de impuesto a la línea de producto '%s'. Para cambiar la alícuota, primero debe remover la anterior.") % line.name)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _fill_sale_purchase_dashboard_data(self, dashboard_data):
        super()._fill_sale_purchase_dashboard_data(dashboard_data)
        for journal in self:
            dashboard_data[journal.id].update({
                'number_to_invoice_orders': 0,
                'sum_to_invoice_orders': '',
            })
            if journal.type == 'sale':
                to_invoice_orders = self.env['sale.order'].search([
                    ('invoice_status', '=', 'to invoice'),
                    ('company_id', '=', journal.company_id.id)
                ])
                count = len(to_invoice_orders)
                amount = sum(to_invoice_orders.mapped('amount_untaxed'))
                formatted_amount = journal.company_id.currency_id.format(amount)
                dashboard_data[journal.id].update({
                    'number_to_invoice_orders': count,
                    'sum_to_invoice_orders': formatted_amount,
                })

    def action_view_to_invoice_orders(self):
        self.ensure_one()
        return {
            'name': _('Pedidos por Facturar'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('invoice_status', '=', 'to invoice'), ('company_id', '=', self.company_id.id)],
            'context': {'create': False},
            'target': 'current',
        }

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(SaleOrder, self).create(vals_list)

    def write(self, vals):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(SaleOrder, self).write(vals)

    def unlink(self):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(SaleOrder, self).unlink()

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(PurchaseOrder, self).create(vals_list)

    def write(self, vals):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(PurchaseOrder, self).write(vals)

    def unlink(self):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(PurchaseOrder, self).unlink()

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(AccountPayment, self).create(vals_list)

    def write(self, vals):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(AccountPayment, self).write(vals)

    def unlink(self):
        if not self.env.su and self.env.user.has_group('l10n_ve_audit.group_fiscal_auditor'):
            raise UserError(_("Los auditores fiscales del SENIAT tienen acceso estrictamente de solo lectura."))
        return super(AccountPayment, self).unlink()
