from odoo import api, fields, models, _, Command

class ResCompany(models.Model):
    _inherit = "res.company"

    currency_id_dif = fields.Many2one("res.currency",
                                      string="Moneda Dual Ref.",
                                      default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')],
                                                                                           limit=1), )
    igtf_divisa_porcentage = fields.Float(string='Porcentaje IGTF', default=3.0)

    bcv_retry_enabled = fields.Boolean(
        string="Activar reintento automático de tasa BCV",
        default=False,
        help="Si la sincronización con el BCV falla, se reintentará automáticamente "
             "según el intervalo configurado en el cron de reintento hasta obtener la tasa exitosamente.",
    )
    bcv_retry_pending = fields.Boolean(
        string="Reintento BCV pendiente",
        default=False,
        help="Campo técnico. Se activa automáticamente cuando falla la sincronización del BCV.",
    )