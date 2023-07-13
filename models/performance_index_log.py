from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PerformanceIndexLog(models.Model):
    _name = 'performance_index.log'
    _description = 'Registro de índices de rendimiento'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Gestión', compute='compute_management', store=True)
    index = fields.Float(string='Índice', digits=(16,4), track_visibility='always')
    management_date = fields.Date(string='Fecha de registro', track_visibility='always')
    state = fields.Selection([('draft', 'Borrador'), ('validate', 'Validado')], default='draft')

    @api.depends('management_date')
    def compute_management(self):
        for record in self:
            record.name = record.management_date.strftime('%Y') if record.management_date else 'Sin fecha'

    def validate_management_index(self):
        self.state = 'validate'

    def draft_management_index(self):
        self.state = 'draft'