from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PerformanceManagement(models.Model):
    _name = 'performance.management'
    _description = 'Gestión de rendimientos de aportes'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Gestion')
    index = fields.Float(string='Índice', digits=(16,4))
    management_date = fields.Date(string='Fecha de registro')
    management = fields.Char(string='Gestión')
    contributions_total = fields.Float(string='Total de aportes')
    yield_amount = fields.Float(string='Monto de rendimiento')
    partner_payroll_id = fields.Many2one('partner.payroll', string='Rendimientos')

    def create(self, data_list):
        a = 1
        res = super(PerformanceManagement, self).create(data_list)
        return res


