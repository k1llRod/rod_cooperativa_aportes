# models/performance_yield_batch.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from server.odoo.tools.populate import compute


class PerformanceYieldBatch(models.Model):
    _name = 'performance.yield.batch'
    _description = 'Lote de Rendimiento por Aportes'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Correlativo', readonly=True, copy=False, default='Nuevo', tracking=True)
    description = fields.Char(string='Descripción', required=True, tracking=True)
    date_start = fields.Date(string='Fecha inicio', required=True, tracking=True)
    date_end = fields.Date(string='Fecha fin', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id.id, required=True)


    # Líneas por cuenta contable
    account_account_line_ids = fields.One2many(
        'performance.yield.account.line', 'batch_id', string='Cuentas y saldos'
    )
    period_payroll_performance_ids = fields.One2many(
        'period.payroll.performance', 'batch_id', string='Periodos de planilla asociados'
    )
    contributions_anual_partner_ids = fields.One2many(
        'contributions.anual.partner', 'batch_id', string='Aportes anuales por asociado'
    )

    total_balance = fields.Monetary(
        string='Saldo total', currency_field='currency_id',
        compute='_compute_total_balance', store=True
    )

    enabled_payroll_service_active_count = fields.Integer(
        string='Planillas habilitadas servicio activo', compute='_compute_enabled_payroll_count'
    )
    enabled_payroll_service_category_a = fields.Integer(
        string='Planillas habilitadas categoría A', compute='_compute_enabled_payroll_count'
    )
    amount_total_mandatory_contribution_certificate = fields.Monetary(
        string='Total monto certificado aportes obligatorios',
        currency_field='currency_id',
        compute='_compute_totals_from_periods', store=True
    )
    amount_total_voluntary_contribution_certificate = fields.Monetary(
        string='Total monto certificado aportes voluntarios',
        currency_field='currency_id',
        compute='_compute_totals_from_periods', store=True
    )
    amount_total_yield_certificate = fields.Monetary(
        string='Total monto certificados',
        currency_field='currency_id',
        compute='_compute_totals_from_periods', store=True
    )
    factor = fields.Float(string='Factor de rendimiento (%)',
                          digits=(12, 9),
                          compute='_compute_factor',
                          store=True,
                          help='Factor de rendimiento aplicado sobre los aportes para calcular el rendimiento.')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Procesado'),
        ('cancel', 'Cancelado'),
    ], default='draft', tracking=True)


    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') in (False, 'Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code('performance.yield.batch') or 'Nuevo'
        return super().create(vals)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end and rec.date_start and rec.date_end < rec.date_start:
                raise ValidationError(_('La fecha fin no puede ser anterior a la fecha inicio.'))

    @api.depends('account_account_line_ids.balance')
    def _compute_total_balance(self):
        for rec in self:
            rec.total_balance = abs(sum(rec.account_account_line_ids.mapped('balance')))

    def _compute_enabled_payroll_count(self):
        payroll = self.env['partner.payroll']
        for rec in self:
            rec.enabled_payroll_service_active_count = len(rec.contributions_anual_partner_ids.filtered(lambda x: x.partner_status_especific == 'active_service'))
            rec.enabled_payroll_service_category_a = len(rec.contributions_anual_partner_ids.filtered(lambda x: x.partner_status_especific == 'passive_reserve_a'))
    # Botón opcional para (re)calcular todas las líneas actuales
    def action_recompute_lines(self):
        for rec in self:
            rec.account_account_line_ids._recompute_from_parent_dates()

    # def action_calculate(self):
    #     self.ensure_one()
    #     if not self.date_start or not self.date_end:
    #         raise ValidationError(_('Debe definir un rango de fechas válido para calcular el rendimiento.'))
    #     self.account_account_line_ids._recompute_from_parent_dates()

    def action_calculate(self):
        self.ensure_one()
        date_init = fields.Date.from_string("2023-01-01")
        if not self.date_start or not self.date_end:
            raise ValidationError(_('Debe definir un rango de fechas válido para calcular el rendimiento.'))

        # Si ya tienes líneas por cuenta, las recalculas (tu lógica actual)
        self.account_account_line_ids._recompute_from_parent_dates()

        # === Nuevo: consolidado mensual desde payroll.payments ===
        #
        allowed_states = ['ministry_defense']

        domain = [
            ('date_pivote', '>=', self.date_start),
            ('date_pivote', '<=', self.date_end),
            ('partner_status_especific', 'in', ['active_service']),
            ('state', 'in', allowed_states),
        ]
        allowed_states = ['transfer', 'ministry_defense','contribution_interest','capital_initial']

        domain_partner = [
            ('date_pivote', '>=', date_init),
            ('date_pivote', '<=', self.date_end),
            ('partner_status_especific', 'in', ['active_service', 'passive_reserve_a']),
            ('partner_payroll_id.state', 'in', ['process']),
            ('state', 'in', allowed_states),
        ]

        grouped = self.env['payroll.payments'].read_group(
            domain=domain,
            fields=[
                'mandatory_contribution_certificate:sum',
                'voluntary_contribution_certificate:sum',
                'id:count',
            ],
            groupby=['period_register'],
            lazy=False,
        )
        grouped_partner = self.env['payroll.payments'].read_group(
            domain=domain_partner,
            fields=[
                'partner_payroll_id',
                'partner_name',
                'partner_code_contact',
                'partner_status_especific',
                'mandatory_contribution_certificate:sum',
                'voluntary_contribution_certificate:sum',
                'id:count',
            ],
            groupby=['partner_payroll_id'],
            lazy=False,
        )

        # Limpia y crea las líneas mensuales
        self.period_payroll_performance_ids.unlink()
        self.contributions_anual_partner_ids.unlink()

        lines_vals = []
        lines_partner_vals = []
        for g in grouped:
            period = g.get('period_register')
            lines_vals.append((0, 0, {
                'name': period or '',
                # 'count_payments': g.get('id_count', 0) or 0,
                'date_start': self.date_start if self.date_start else False,
                'date_end': self.date_end if self.date_end else False,
                'batch_id': self.id,
                'partner_status_especific': 'active_service',  # Asumimos servicio activo para
                'total_mandatory_contribution': g.get('mandatory_contribution_certificate', 0.0) or 0.0,
                'total_voluntary_contribution': g.get('voluntary_contribution_certificate', 0.0) or 0.0,
            }))
        if lines_vals:
            self.write({'period_payroll_performance_ids': lines_vals})

        for g in grouped_partner:
            lines_partner_vals.append((0, 0, {
                'partner_payroll_ids': g.get('partner_payroll_id')[0] if g.get('partner_payroll_id') else False,
                'total_mandatory_contribution': g.get('mandatory_contribution_certificate', 0.0) or 0.0,
                'total_voluntary_contribution': g.get('voluntary_contribution_certificate', 0.0) or 0.0,
                'year': self.date_end.year if self.date_end else False,
                'payroll_count': g['__count'] or 0,
            }))
        if lines_partner_vals:
            self.write({'contributions_anual_partner_ids': lines_partner_vals})

        self.state = 'draft'

    @api.depends('contributions_anual_partner_ids')
    def _compute_totals_from_periods(self):
        for rec in self:
            rec.amount_total_mandatory_contribution_certificate = sum(
                rec.contributions_anual_partner_ids.mapped('total_mandatory_contribution')
            )
            rec.amount_total_voluntary_contribution_certificate = sum(
                rec.contributions_anual_partner_ids.mapped('total_voluntary_contribution')
            )
            rec.amount_total_yield_certificate = (
                rec.amount_total_mandatory_contribution_certificate +
                rec.amount_total_voluntary_contribution_certificate
            )

    @api.depends('amount_total_yield_certificate', 'total_balance')
    def _compute_factor(self):
        for rec in self:
            if rec.amount_total_yield_certificate > 0 and rec.total_balance > 0:
                rec.factor = rec.total_balance / rec.amount_total_yield_certificate
            else:
                rec.factor = 0.0





