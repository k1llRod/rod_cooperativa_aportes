from odoo import models, fields, api, _

class PayContribution(models.TransientModel):
    _name = 'pay.contribution'
    _description = 'Pay Contribution'

    # Campos del wizard
    partner_payroll_id = fields.Integer(string='Partner payroll id', required=True)