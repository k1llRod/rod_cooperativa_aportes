from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PerformanceManagement(models.Model):
    _name = 'performance.management'
    _description = 'Gestión de rendimientos de aportes'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    index = fields.Float(string='Índice')
    management_date = fields.Date(string='Fecha de gestión')
    management = fields.Char(string='Gestión')
    yield_amount = fields.Float(string='Monto de rendimiento')
    performance_management_id = fields.Many2one('partner.payroll', string='Rendimientos')

    def create(self, data_list):
        a = 1
        res = super(PerformanceManagement, self).create(data_list)
        return res


