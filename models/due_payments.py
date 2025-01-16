from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re


class DuePayments(models.Model):
    _name = 'due.payments'
    _description = 'Due Payments'

    name = fields.Char(string='Periodo')
    d_miscellaneous_income = fields.Integer(string='D. inscripcion', digits=(12, 2))
    d_regulation_cup = fields.Float(string='D. tasa de regulacion', digits=(12, 2))
    d_mandatory_contribution = fields.Float(string='D. aporte obligatorio', digits=(12, 2))
    d_voluntary_contribution = fields.Float(string='Aporte voluntario', digits=(12, 2))
    d_post_mortem = fields.Float(string='D. post morte', digits=(12, 2))
    gestion = fields.Integer(string='Gestion')
    d_total = fields.Float(string='Total debe', digits=(12, 2))
    due_partner_payroll_id = fields.Many2one('partner.payroll', string='Pagos adelantados')
