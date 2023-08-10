from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re


class PayrollPayment(models.Model):
    _name = 'payroll.payment'
    _description = 'Pagos de planilla'

    name = fields.Char(string='ID aporte')
    partner_payrolls_id = fields.Many2one('partner.payroll', string='Planilla de socio')
    amount = fields.Float(string='Monto')