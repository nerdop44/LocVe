# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime

class IgtfReportWizard(models.TransientModel):
    _name = "igtf.report.wizard"
    _description = "Reporte Consolidado IGTF SENIAT"

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    date_from = fields.Date(
        string="Fecha Desde",
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1),
    )
    date_to = fields.Date(
        string="Fecha Hasta",
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )

    def action_generate_report(self):
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("state", "=", "posted"),
            ("is_igtf_on_foreign_exchange", "=", True),
        ]
        
        payments = self.env["account.payment"].search(domain, order="date asc, id asc")
        
        return {
            "name": _("Consolidado IGTF SENIAT"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "list,form",
            "domain": [("id", "in", payments.ids)],
            "context": {
                "create": False,
                "delete": False,
                "search_default_posted": 1,
            },
        }
