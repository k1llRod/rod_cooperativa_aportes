from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PeriodPayrollPerformance(models.Model):
    _name = 'period.payroll.performance'
    _description = 'Periodo de Planilla para Rendimiento'
    _order = 'date_start desc'

    name = fields.Char(string='Periodo', required=True)
    date_start = fields.Date(string='Fecha inicio', required=True)
    date_end = fields.Date(string='Fecha fin', required=True)
    description = fields.Char(string='Descripción')
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ], string='Tipo de asociado',
                                                    store=True,
                                                    track_visibility="always")
    percentage_yield = fields.Integer(string='Porcentaje de rendimiento (%)', required=True, default=100)
    total_mandatory_contribution = fields.Float(string='Total aportes obligatorios')
    total_voluntary_contribution = fields.Float(string='Total aportes voluntarios')
    total_contribution = fields.Float(string='Total aportes', compute='_compute_total_contribution', store=True)
    batch_id = fields.Many2one('performance.yield.batch', string='Lote de rendimiento')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado')], default='draft', tracking=True)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin.")

    @api.depends('total_mandatory_contribution', 'total_voluntary_contribution')
    def _compute_total_contribution(self):
        for record in self:
            record.total_contribution = record.total_mandatory_contribution + record.total_voluntary_contribution