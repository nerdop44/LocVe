# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

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
            "|", "|",
            ("is_igtf_on_foreign_exchange", "=", True),
            ("igtf_amount", ">", 0.0),
            ("journal_id.is_igtf", "=", True),
        ]
        
        payments = self.env["account.payment"].search(domain, order="date asc, id asc")
        
        view_id = self.env.ref("l10n_ve_igtf.view_igtf_consolidated_payment_tree", raise_if_not_found=False)
        
        res = {
            "name": _("Consolidado IGTF SENIAT (%s al %s)") % (self.date_from, self.date_to),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "list,form",
            "domain": [("id", "in", payments.ids)],
            "context": {
                "create": False,
                "delete": False,
            },
        }
        if view_id:
            res["views"] = [(view_id.id, "list"), (False, "form")]
        return res
