# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class L10nVeDeliveryGuideWizard(models.TransientModel):
    _name = 'l10n_ve.delivery.guide.wizard'
    _description = 'Wizard para ingresar datos de la Guía de Despacho'

    picking_id = fields.Many2one('stock.picking', string="Operación de Stock", required=True)
    l10n_ve_guide_number = fields.Char(string="Número de Guía de Despacho", required=True)
    l10n_ve_carrier_name = fields.Char(string="Nombre del Transportista", required=True)
    l10n_ve_carrier_vat = fields.Char(string="RIF/Cédula del Transportista", required=True)
    l10n_ve_vehicle_plate = fields.Char(string="Placa del Vehículo", required=True)
    l10n_ve_vehicle_brand = fields.Char(string="Marca/Modelo del Vehículo", required=True)
    l10n_ve_starting_point = fields.Text(string="Dirección de Salida", required=True)
    l10n_ve_ending_point = fields.Text(string="Dirección de Llegada", required=True)

    def action_confirm(self):
        self.ensure_one()
        # Escribir los valores actualizados de vuelta en el stock.picking
        self.picking_id.write({
            'l10n_ve_guide_number': self.l10n_ve_guide_number,
            'l10n_ve_carrier_name': self.l10n_ve_carrier_name,
            'l10n_ve_carrier_vat': self.l10n_ve_carrier_vat,
            'l10n_ve_vehicle_plate': self.l10n_ve_vehicle_plate,
            'l10n_ve_vehicle_brand': self.l10n_ve_vehicle_brand,
            'l10n_ve_starting_point': self.l10n_ve_starting_point,
            'l10n_ve_ending_point': self.l10n_ve_ending_point,
        })
        # Ejecutar la acción de impresión del reporte de Guía de Despacho
        return self.env.ref('l10n_ve_invoice.action_report_delivery_guide').report_action(self.picking_id)
