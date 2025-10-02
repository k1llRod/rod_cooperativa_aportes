from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ContributionsAnualPartner(models.Model):
    _name = 'contributions.anual.partner'
    _description = 'Aportes Anuales por Asociado'
    _order = 'year desc'

    name=fields.Char(string='Descripción')
    date_init = fields.Date(string='Fecha de inicio', default="2023-01-01", required=True)
    partner_payroll_ids = fields.Many2one('partner.payroll', string='Asociado', required=True)
    partner_id = fields.Many2one(related='partner_payroll_ids.partner_id', string='Asociado', store=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado',
                                                related='partner_payroll_ids.partner_id.partner_status_especific',
                                                store=True)
    date_burn_partner = fields.Datetime(related='partner_payroll_ids.date_burn_partner', string='Fecha de filiacion', store=True)
    total_mandatory_contribution = fields.Float(string='Total aportes obligatorios', default=0.0)
    total_voluntary_contribution = fields.Float(string='Total aportes voluntarios', default=0.0)
    total_contribution = fields.Float(string='Total aportes', compute='_compute_total_contribution', store=True)
    batch_id = fields.Many2one('performance.yield.batch', string='Lote de rendimiento')
    payroll_count = fields.Integer('N. Aportaciones')
    year = fields.Integer(string='Año', required=True)
    factor = fields.Float(string='Factor de rendimiento (%)', digits=(12, 9), default=0.0,
                          help='Factor de rendimiento aplicado sobre los aportes para calcular el rendimiento.')
    amount_factor_calculate_yield = fields.Float(string='Monto rendimiento calculado', default=0.0, compute='_compute_amount_factor_calculate_yield', store=True,digits=(12, 2))

    _sql_constraints = [
        ('unique_partner_year', 'unique(partner_payroll_ids,batch_id)', 'Ya existe un registro para este asociado en el año especificado.')
    ]

    @api.depends('total_mandatory_contribution', 'total_voluntary_contribution')
    def _compute_total_contribution(self):
        for record in self:
            record.total_contribution = record.total_mandatory_contribution + record.total_voluntary_contribution

    @api.depends('total_contribution', 'factor')
    def _compute_amount_factor_calculate_yield(self):
        for record in self:
            record.amount_factor_calculate_yield = record.total_contribution * record.factor
