from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import re


class PartnerPayroll(models.Model):
    _name = 'partner.payroll'
    _description = 'Planilla de socio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    state = fields.Selection([('draft', 'Borrador'),
                              ('process', 'En proceso'),
                              ('process_finalized', 'Proceso liquidacion'),
                              ('finalized', 'Liquidado'),
                              ('unassociated', 'No asociado')],
                             default='draft', track_visibility='always')
    partner_id = fields.Many2one('res.partner', string='Socio')
    partner_name = fields.Char(string='Nombre firma', compute='_compute_formatted_name')

    partner_status = fields.Selection([('active', 'Activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive', 'Servicio pasivo'),
                                       ('leave', 'Baja')], string="Situacion general",
                                      related='partner_id.partner_status', store=True, track_visibility="always")
    partner_status_historical = fields.Selection([('active', 'Activo'),
                                                  ('active_reserve', 'Reserva activa'),
                                                  ('passive', 'Servicio pasivo'),
                                                  ('leave', 'Baja')], string="Situacion general historico",
                                                 store=True, track_visibility="always")

    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado',
                                                related='partner_id.partner_status_especific', store=True,
                                                track_visibility="always")

    partner_status_especific_historical = fields.Selection([('active_service', 'Servicio activo'),
                                                            ('letter_a', 'Letra "A" de disponibilidad'),
                                                            ('passive_reserve_a', 'Pasivo categoria "A"'),
                                                            ('passive_reserve_b', 'Pasivo categoria "B"'),
                                                            ('leave', 'Baja')], string='Tipo de asociado historico',
                                                           store=True, track_visibility="always")
    category_partner = fields.Char(string='Grado', related='partner_id.category_partner_id.name', store=True)
    code_contact = fields.Char(string='Código de asociado', related='partner_id.code_contact', store=True)
    vat = fields.Char(string='CI', related='partner_id.vat')
    city = fields.Char(string='Ciudad', related='partner_id.city', store=True)
    date_registration = fields.Datetime(string='Fecha de registro')
    date_burn_partner = fields.Datetime(string='Fecha de afiliacion')
    date_finalized = fields.Datetime(string='Fecha de liquidacion')
    total_contribution = fields.Float(string='Total aportado')
    advanced_payments = fields.Float(string='Tasa de regulación Adelantado')
    payroll_payments_ids = fields.One2many('payroll.payments', 'partner_payroll_id', string='Pagos individuales',
                                           tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        default=lambda self: self.env.company, index=True
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        related='company_id.currency_id', store=True, readonly=True
    )

    capital_initial = fields.Monetary(
        string='Capital inicial', currency_field='currency_id',
        compute='compute_contributions', store=True
    )
    miscellaneous_income = fields.Float(string='Gastos adicional', compute='compute_miscellaneous_income')
    mandatory_contribution_pending = fields.Integer(string='Aportes obligatorios pendientes',
                                                    compute='compute_miscellaneous_income')
    advance_mandatory_certificate = fields.Float(string='Cert. Aport. Oblig. Adelantado')
    total = fields.Float(string='Total', store=True)
    count_pay_contributions = fields.Integer(string='Cantidad de pagos realizados',
                                             compute="compute_count_pay_contributions", store=True)
    advance_regulation_cup = fields.Integer(string='Tasa de regulación adelantado',
                                            compute="compute_count_pay_contributions")
    updated_partner = fields.Boolean(string='Actualizado', compute="compute_updated_partner")
    tree_updated_partner = fields.Boolean(string='Actualizado', related='updated_partner')
    outstanding_payments = fields.Integer(string='Pagos pendientes', compute="compute_updated_partner", store=True)
    outstanding = fields.Integer(string='Pagos pendientes', compute="calculate_month_difference")

    voluntary_contribution_certificate_total = fields.Monetary(
        string='Cert. Aport. Vol. Total', currency_field='currency_id',
        compute='compute_count_pay_contributions', store=True
    )
    mandatory_contribution_certificate_total = fields.Monetary(
        string='Cert. Aport. Oblig. total', currency_field='currency_id',
        compute='compute_count_pay_contributions', store=True
    )
    other_contribution_total = fields.Monetary(
        string='Otros aportes', currency_field='currency_id', store=True
    )
    surpluses_total = fields.Monetary(
        string='Total excedentes', currency_field='currency_id', store=True
    )
    contribution_total = fields.Monetary(string='Aporte total', currency_field='currency_id', store=True)
    contribution_total_excluded = fields.Float(string='Aporte total excluido', store=True)

    performance_management_total = fields.Float(string='Rendimiento total',
                                                compute='compute_performance_management_total')
    performance_management_ids = fields.One2many('performance.management', 'partner_payroll_id', string='Rendimientos')
    advanced_payments_ids = fields.One2many('advance.payments', 'advanced_partner_payroll_id',
                                            string='Pagos adelantados')
    due_payments_ids = fields.One2many('due.payments', 'due_partner_payroll_id', string='Pagos pendientes')

    # CORRECCIÓN DE CAMPOS COMPUTE (Mapeo de saldos)
    balance_advance_contribution_passive = fields.Float(string='Saldo aportes pasivos',
                                                        compute='compute_balance_advance')
    balance_advance_regulation_cup = fields.Float(string='Saldo tasa de regulación', compute='compute_balance_advance')
    balance_advance_mandatory_contribution = fields.Float(string='Saldo aportes obligatorios',
                                                          compute='compute_balance_advance')

    count_mandatory_contribution_certificate = fields.Integer(string='Contador de certificados de aportes obligatorios',
                                                              compute='compute_contributions')
    journal_id = fields.Many2one('account.journal', string='Diario')
    account_income_id = fields.Many2one('account.account', string='Ingreso',
                                        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
                                            'rod_cooperativa_aportes.account_income_id'))
    account_inscription_id = fields.Many2one('account.account', string='Inscripcion',
                                             default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
                                                 'rod_cooperativa_aportes.account_inscription_id'))
    account_regulation_cup_id = fields.Many2one('account.account', string='Tasa de regulacion',
                                                default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
                                                    'rod_cooperativa_aportes.account_regulation_cup_id'))
    account_mandatory_contribution_id = fields.Many2one('account.account', string='Aportes obligatorios',
                                                        default=lambda self: self.env[
                                                            'ir.config_parameter'].sudo().get_param(
                                                            'rod_cooperativa_aportes.account_mandatory_contribution_id'))
    account_voluntary_contribution_id = fields.Many2one('account.account', string='Aportes voluntarios',
                                                        default=lambda self: self.env[
                                                            'ir.config_parameter'].sudo().get_param(
                                                            'rod_cooperativa_aportes.account_voluntary_contribution_id'))

    payment_type = fields.Selection([('cossmil_discount', 'Descuento COSSMIL'),
                                     ('voluntary_contribution', 'Aporte voluntario'),
                                     ('voluntary_contribution_discount', 'Descuento devolucion de aportes')],
                                    string='Tipo de pago')
    since_payment = fields.Date(string='Desde')
    until_payment = fields.Date(string='Hasta')
    amount_type = fields.Float(string='Aporte voluntario post mortem', default=0.0)
    difference_year = fields.Integer(string='Diferencia de años', compute='compute_difference_year')
    year_now = fields.Integer(string='Año actual', compute='compute_difference_year')

    missing_payments = fields.Integer(string='Pagos faltantes')
    must_regulation_rate = fields.Float(string='Debe tasa de regulación')
    must_mandatory_contribution = fields.Float(string='Debe aporte obligatorio')
    must_voluntary_contribution = fields.Float(string='Debe aporte voluntario')
    must_post_mortem = fields.Float(string='Debe aporte post mortem')
    must_total = fields.Float(string='Debe total')
    must_gestion = fields.Integer(string='Debe gestion')

    partner_state = fields.Selection([('draft', 'Borrador'),
                                      ('verificate', 'Verificación'),
                                      ('activate', 'Socio activo'),
                                      ('external', 'Externo'),
                                      ('rejected', 'Rechazado'),
                                      ('unsubscribe', 'Baja'),
                                      ('deceased', 'Fallecido')],
                                     string='Estado', default='draft', related='partner_id.state', store=True)

    afiliated_time = fields.Integer(string='Tiempo afiliado', compute='_onchange_name')

    gloss_disengagement = fields.Text(string="Observaciones Baja")
    type_disengagements = fields.Selection([('fallecimiento', 'Fallecimiento'),
                                            ('retiro_voluntario', 'Retiro voluntario'),
                                            ('pase_servicio_pasivo', 'Pase al servicio pasivo'),
                                            ('abandono', 'Abandono'),
                                            ('expulsion', 'Expulsion')],
                                           string="Baja por", store=True)
    date_disengagements = fields.Date(string='Fecha de baja', default=lambda self: datetime.now().date())
    date_unassociated = fields.Date(string='Fecha de no asociado')
    state_finalize = fields.Selection([('borrador', 'Borrador'),
                                       ('hecho', 'Hecho')], default='borrador', string='Estado de liquidacion')

    finalize_contributions_ids = fields.One2many('finalize.contributions', 'partner_payroll_ids',
                                                 string='Liquidaciones')
    partner_status_especific_reorder = fields.Selection([('passive_reserve_a', 'Reserva pasivo "A"'),
                                                         ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                         ], string='Tipo de asociado')

    mount_passive_a = fields.Float(string='Monto Categoria A')
    amount_return = fields.Float(string='Monto Dev.')

    def _compute_total(self):
        for record in self:
            record.total = record.capital_initial + record.voluntary_contribution_certificate_total + record.mandatory_contribution_certificate_total + record.other_contribution_total

    @api.depends('since_payment', 'until_payment')
    def compute_difference_year(self):
        for record in self:
            record.year_now = datetime.now().year
            if record.until_payment:
                record.difference_year = record.until_payment.year + 1
                if record.difference_year < record.year_now:
                    record.difference_year = record.year_now
                if record.until_payment.year < 2023:
                    record.difference_year = 2023
            else:
                record.difference_year = 0

    @api.depends('payroll_payments_ids')
    def compute_miscellaneous_income(self):
        miscellaneous_income_param = self.env['ir.config_parameter'].sudo().get_param(
            'rod_cooperativa_aportes.miscellaneous_income')
        for record in self:
            verify = len(record.payroll_payments_ids.filtered(
                lambda x: (x.state == 'transfer' or x.state == 'ministry_defense') and x.miscellaneous_income > 0))
            if verify == 0:
                record.miscellaneous_income = miscellaneous_income_param
            else:
                record.miscellaneous_income = 0

            periods = self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.month_ids')
            mandatory_contribution = float(record.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.mandatory_contribution_certificate'))
            year_now = datetime.now().year
            filter_periods = re.findall(r'\d+', periods) if periods else []
            count_periods = len(filter_periods)
            count_mandatory_contributions = count_periods * mandatory_contribution
            verificate_payments = record.payroll_payments_ids.filtered(
                lambda x: (
                                      x.state == 'transfer' or x.state == 'ministry_defense') and x.payment_date and x.payment_date.year == year_now)
            sum_verificate_payments = sum(verificate_payments.mapped('mandatory_contribution_certificate'))
            record.mandatory_contribution_pending = count_mandatory_contributions - sum_verificate_payments

    @api.depends('payroll_payments_ids')
    def compute_contributions(self):
        for record in self:
            record.voluntary_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(
                lambda x: (x.state == 'transfer' or x.state == 'ministry_defense' or (
                        x.state == 'partner_return' and x.switch_draf == False))).mapped(
                'voluntary_contribution_certificate'))
            record.count_mandatory_contribution_certificate = len(
                record.payroll_payments_ids.filtered(lambda x: x.mandatory_contribution_certificate > 0))
            record.capital_initial = sum(
                record.payroll_payments_ids.filtered(
                    lambda x: x.state == 'contribution_interest' or x.state == 'capital_initial').mapped(
                    'voluntary_contribution_certificate'))

    def init_payroll_partner_wizard(self):
        context = {
            'default_partner_payroll_id': self.id,
            'default_capital_base': getattr(self, 'capital_base', 0.0),
        }
        return {
            'name': 'Conciliar pagos de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'init.payroll.partner',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def import_payroll(self):
        return {
            'name': 'Conciliar pagos de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'reconcile.contributions',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.depends('partner_id')
    def compute_partner_status(self):
        for record in self:
            record.partner_status = record.partner_id.status

    def wizard_pay_contribution(self):
        context = {
            'default_partner_payroll_id': self.id,
            'default_capital_base': getattr(self, 'capital_base', 0.0),
        }
        return {
            'name': 'Conciliar pagos de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'pay.contribution',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    @api.depends('payroll_payments_ids', 'performance_management_ids')
    def compute_count_pay_contributions(self):
        for record in self:
            record.count_pay_contributions = len(
                record.payroll_payments_ids.filtered(lambda x: x.state != 'draft' and x.state != 'no_contribution'))
            record.mandatory_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(
                lambda x: x.state == 'transfer' or x.state == 'ministry_defense').mapped(
                'mandatory_contribution_certificate'))
            record.voluntary_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(
                lambda x: x.state == 'transfer' or x.state == 'ministry_defense' or (
                        x.state == 'partner_return' and x.switch_draf == False)).mapped(
                'voluntary_contribution_certificate'))
            interest_total = sum(record.performance_management_ids.mapped('yield_amount'))
            record.other_contribution_total = sum(round(c, 2) for c in record.payroll_payments_ids.filtered(
                lambda x: x.state == 'other_contribution' or x.state == 'other_contribution_coaa').mapped(
                'other_contribution'))
            record.surpluses_total = sum(
                record.payroll_payments_ids.filtered(lambda x: x.state == 'surpluses').mapped(
                    'other_contribution'))
            record.amount_return = sum(
                record.payroll_payments_ids.filtered(lambda
                                                         x: (
                                                                        x.state == 'partner_return' or x.state == 'partner_return_credit') and x.switch_draf == False).mapped(
                    'voluntary_contribution_certificate'))
            record.contribution_total = record.voluntary_contribution_certificate_total + record.mandatory_contribution_certificate_total + interest_total + record.capital_initial + record.other_contribution_total + record.surpluses_total + record.amount_return

    def return_draft(self):
        self.state = 'draft'

    def get_month_starts(self, start_date, end_date):
        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()
        result = []
        current = start_date.replace(day=1)
        while current <= end_date:
            result.append(current)
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return result

    @api.depends('payroll_payments_ids', 'date_burn_partner', 'partner_status_especific', 'until_payment')
    def compute_updated_partner(self):
        config_sudo = self.env['ir.config_parameter'].sudo()
        regulation_cup = float(config_sudo.get_param('rod_cooperativa_aportes.regulation_cup', 0))
        mandatory_contribution = float(
            config_sudo.get_param('rod_cooperativa_aportes.mandatory_contribution_certificate', 0))
        today = datetime.now().date()

        for record in self:
            record.updated_partner = False
            record.outstanding_payments = 0
            record.must_regulation_rate = 0.0
            record.must_mandatory_contribution = 0.0
            record.must_total = 0.0
            record.must_gestion = 0

            if not record.date_burn_partner:
                continue

            if record.partner_status_especific not in ['passive_reserve_a', 'passive_reserve_b']:
                date_burn = record.date_burn_partner.date() if isinstance(record.date_burn_partner,
                                                                          datetime) else record.date_burn_partner
                diff = relativedelta(today, date_burn)
                diff_months = diff.years * 12 + diff.months

                valid_payments = record.payroll_payments_ids.filtered(
                    lambda x: x.state in ['ministry_defense', 'transfer'] and not x.drawback
                )
                count_payments = len(valid_payments)

                if count_payments >= diff_months and record.state != 'draft':
                    record.updated_partner = True
                    record.outstanding_payments = 0
                else:
                    record.updated_partner = False
                    record.outstanding_payments = diff_months - count_payments
                    record.must_regulation_rate = record.outstanding_payments * regulation_cup
                    record.must_mandatory_contribution = (record.outstanding_payments / 6) * mandatory_contribution
                    record.must_gestion = count_payments / 12

                    post_mortem_val = getattr(record, 'must_post_mortem', 0.0)
                    record.must_total = record.must_regulation_rate + record.must_mandatory_contribution + post_mortem_val

    def _update_due_payments(self):
        config_sudo = self.env['ir.config_parameter'].sudo()
        regulation_cup = float(config_sudo.get_param('rod_cooperativa_aportes.regulation_cup', 0))
        mandatory_contribution = float(
            config_sudo.get_param('rod_cooperativa_aportes.mandatory_contribution_certificate', 0))
        today = datetime.now().date()

        for record in self:
            if not record.date_burn_partner:
                continue

            if record.partner_status_especific == 'passive_reserve_b':
                self.env['due.payments'].search([('due_partner_payroll_id', '=', record.id)]).unlink()

                año_base = 2023
                date_burn = record.date_burn_partner.date() if isinstance(record.date_burn_partner,
                                                                          datetime) else record.date_burn_partner
                if date_burn.month > 9:
                    gestion_ini = max(date_burn.year + 1, año_base)
                else:
                    gestion_ini = max(date_burn.year, año_base)

                domain_ant = [
                    ('partner_id', '=', record.partner_id.id),
                    ('state', 'in', ['process_finalized', 'finalized']),
                    ('id', '!=', record.id)
                ]
                anteriores_count = self.env['partner.payroll'].search_count(domain_ant)
                sw_primera_gestion = True if anteriores_count == 0 else False

                for gestion_process in range(gestion_ini, today.year + 1):
                    payments_year = record.payroll_payments_ids.filtered(
                        lambda x: x.period_register and str(gestion_process) in str(x.period_register)
                    )

                    sum_reg_cup = sum(payments_year.mapped('regulation_cup'))
                    sum_mandatory = sum(payments_year.mapped('mandatory_contribution_certificate'))
                    sum_voluntary = sum(payments_year.mapped('voluntary_contribution_certificate'))

                    cal_reg_cup = max((regulation_cup * 12) - sum_reg_cup, 0)
                    cal_mandatory = max((mandatory_contribution * 2) - sum_mandatory, 0)

                    cal_misc = 0.0
                    if sw_primera_gestion and record.miscellaneous_income != 0:
                        sum_misc = sum(payments_year.mapped('miscellaneous_income'))
                        cal_misc = max(10.0 - sum_misc, 0)
                        sw_primera_gestion = False

                    cal_post_mortem = 0.0
                    limit_year = record.until_payment.year if record.until_payment else 0
                    if gestion_process > limit_year:
                        cal_post_mortem = max(167.28 - sum_voluntary, 0)

                    self.env['due.payments'].create({
                        'name': f"Gestión {gestion_process}",
                        'd_miscellaneous_income': cal_misc,
                        'd_regulation_cup': cal_reg_cup,
                        'd_mandatory_contribution': cal_mandatory,
                        'd_voluntary_contribution': sum_voluntary,
                        'd_post_mortem': cal_post_mortem,
                        'd_total': round(cal_misc + cal_reg_cup + cal_mandatory + cal_post_mortem, 2),
                        'due_partner_payroll_id': record.id,
                        'gestion': gestion_process
                    })

            elif record.partner_status_especific == 'passive_reserve_a':
                self.env['due.payments'].search([('due_partner_payroll_id', '=', record.id)]).unlink()

                last_pay = record.payroll_payments_ids.sorted('date_pivote', reverse=True)[:1]
                if last_pay and last_pay.date_pivote:
                    start_calc_date = last_pay.date_pivote + relativedelta(months=1)
                else:
                    start_calc_date = record.date_burn_partner

                if isinstance(start_calc_date, datetime):
                    start_calc_date = start_calc_date.date()

                months_to_bill = record.get_month_starts(start_calc_date, today) or []

                for month_date in months_to_bill:
                    d_total = record.mount_passive_a or 0.0
                    self.env['due.payments'].create({
                        'name': month_date.strftime('%m/%Y'),
                        'd_total': round(d_total, 2),
                        'due_partner_payroll_id': record.id,
                        'gestion': month_date.year,
                    })

    # FUSIÓN UNIFICADA DE MÉTODOS CREATE CRÍTICOS
    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('partner.payroll')
        vals['name'] = name
        res = super(PartnerPayroll, self).create(vals)
        res._update_due_payments()
        return res

    def write(self, vals):
        res = super(PartnerPayroll, self).write(vals)
        fields_to_check = ['payroll_payments_ids', 'date_burn_partner', 'partner_status_especific', 'until_payment']
        if any(f in vals for f in fields_to_check):
            self._update_due_payments()
        return res

    def print_report_total(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Reporte procesado de forma correcta."),
                'sticky': False,
            }
        }

    @api.depends('payroll_payments_ids', 'date_burn_partner', 'due_payments_ids')
    def calculate_month_difference(self):
        for record in self:
            count_payments = 0
            if not record.date_burn_partner:
                record.outstanding = 0
                continue

            diff = relativedelta(datetime.now(), record.date_burn_partner)
            diff_months = diff.years * 12 + diff.months

            if record.partner_status_especific == 'active_service':
                count_payments = len(record.payroll_payments_ids.filtered(
                    lambda x: x.state in ('ministry_defense', 'transfer') and not x.drawback))
                record.outstanding = diff_months - count_payments
            elif record.partner_status_especific == 'passive_reserve_a':
                count_payments = len(
                    record.payroll_payments_ids.filtered(lambda x: x.state == 'transfer' and not x.drawback))
                record.outstanding = diff_months - count_payments
            elif record.partner_status_especific == 'passive_reserve_b':
                count_payments = len(record.due_payments_ids.filtered(lambda x: x.d_total > 0))
                record.outstanding = count_payments
                diff_months = 0 if count_payments == 0 else diff_months

            if count_payments >= diff_months and record.state != 'draft':
                record.updated_partner = True
                record.outstanding = 0
            else:
                if record.partner_status_especific == 'passive_reserve_b':
                    record.updated_partner = False
                    record.outstanding = count_payments
                else:
                    record.outstanding = diff_months - count_payments

    def select_init_partner_payroll(self):
        for record in self:
            if record.partner_status == 'active' and record.state == 'draft':
                if not record.date_burn_partner:
                    record.date_burn_partner = datetime.now()
                else:
                    record.state = 'process'

    def validate_partner_passive(self):
        for record in self:
            record.state = 'process'

    def init_partner_payroll_interest(self):
        context = {'default_partner_payroll_id': self.id}
        return {
            'name': 'Establecer interes de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'set.interes',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }

    def assign_performance(self):
        return {
            'name': 'Establecer interes de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'set.management',
            'view_mode': 'form',
            'target': 'new',
        }

    def resume_process(self):
        for record in self:
            if record.date_burn_partner:
                record.state = 'process'

    @api.depends('performance_management_ids')
    def compute_performance_management_total(self):
        for record in self:
            record.performance_management_total = sum(record.performance_management_ids.mapped('yield_amount'))

    # CORRECCIÓN DE LA ASIGNACIÓN DE VARIABLES CONTABLES SOBRE CAMPOS REALES
    def compute_balance_advance(self):
        for record in self:
            record.balance_advance_contribution_passive = record.contribution_total - record.performance_management_total
            record.balance_advance_regulation_cup = 0.0
            record.balance_advance_mandatory_contribution = 0.0

    def finalized_payroll(self):
        total_contributions = (self.capital_initial + self.voluntary_contribution_certificate_total +
                               self.mandatory_contribution_certificate_total + self.performance_management_total +
                               self.other_contribution_total + self.surpluses_total + self.amount_return)

        loan_id = self.env['loan.application'].search(
            [('partner_id', '=', self.partner_id.id), ('state', '=', 'progress')], limit=1)

        total_loan_capital_bolivianos = loan_id.balance_capital * loan_id.value_dolar if loan_id else 0.0
        total_balance_total_interest_month_bolivianos = loan_id.balance_total_interest_month * loan_id.value_dolar if loan_id else 0.0

        context = {
            'default_partner_payroll_id': self.id,
            'default_total_mandatory_contributions_certificate': self.mandatory_contribution_certificate_total,
            'default_total_voluntary_contributions_certificate': self.voluntary_contribution_certificate_total,
            'default_total_performance_contributions': self.performance_management_total,
            'default_total_other_contributions': self.other_contribution_total,
            'default_total_balance_capital': self.contribution_total,
            'default_capital_initial': self.capital_initial,
            'default_total_contributions': total_contributions,
            'default_total_surpluses': self.surpluses_total,
            'default_loan_application_id': loan_id.id if loan_id else False,
            'default_total_loan_capital': loan_id.balance_capital if loan_id else 0.0,
            'default_total_balance_total_interest_month': loan_id.balance_total_interest_month if loan_id else 0.0,
            'default_default_dolar': loan_id.value_dolar if loan_id else 0.0,
            'default_total_loan_capital_bolivianos': total_loan_capital_bolivianos,
            'default_total_balance_total_interest_month_bolivianos': total_balance_total_interest_month_bolivianos,
        }
        return {
            'name': 'Formulario de liquidacion',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.finalized.contributions',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }

    def publish_accouting_entries(self):
        for record in self:
            payments = record.payroll_payments_ids
            for payment in payments:
                income = record.account_income_id
                inscription = record.account_inscription_id
                regulation_cup = record.account_regulation_cup_id
                mandatory_contribution = record.account_mandatory_contribution_id
                voluntary_contribution = record.account_voluntary_contribution_id
                payment.create_account_move(income, inscription, regulation_cup, mandatory_contribution,
                                            voluntary_contribution)

    def wizard_payroll_return(self):
        context = {
            'default_name': self.name,
            'default_date_pivote': datetime.now(),
            'default_payment_date': datetime.now(),
            'default_mount': self.total,
            'default_glosa': 'Devolucion de aportes',
            'default_partner_payroll_id': self.id,
        }
        return {
            'name': 'Pago de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.payroll.return',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }

    @api.depends('date_burn_partner')
    def _onchange_name(self):
        for record in self:
            if record.date_burn_partner:
                year_difference = datetime.now().year - record.date_burn_partner.year
                month_difference = datetime.now().month - record.date_burn_partner.month
                total = year_difference * 12 + month_difference
                record.afiliated_time = total
            else:
                record.afiliated_time = 0

    def exclude_contributions(self):
        total = round(sum(self.payroll_payments_ids.filtered(lambda x: x.state == 'ministry_defense').mapped('income')),
                      2)
        context = {
            'default_partner_payroll_id': self.id,
            'default_total_contributions': total,
        }
        return {
            'name': 'Pago de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.unassociated',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
        }

    def updated_contributions(self):
        for rec in self:
            verificate = rec.payroll_payments_ids.filtered(lambda x: x.state in ('other_contribution', 'surpluses'))
            for record in verificate:
                record.other_contribution = record.income
                record.income = 0
                record.regulation_cup = 0
                record.miscellaneous_income = 0
                record.mandatory_contribution_certificate = 0

    def process_partner_status(self):
        for record in self:
            if record.state == 'process':
                raise ValidationError(_('La planilla de aportes debe estar en un estado "PROCESO DE LIQUIDACION"'))
            if record.type_disengagements == 'fallecimiento':
                record.partner_id.state = 'deceased'
                record.state = 'finalized'
                record.partner_id.glosa = record.gloss_disengagement
                record.partner_id.date_deceased = datetime.now()
                record.state_finalize = 'hecho'
            elif record.type_disengagements in ('retiro_voluntario', 'abandono', 'expulsion'):
                record.partner_id.state = 'unsubscribe'
                record.state = 'finalized'
                record.state_finalize = 'hecho'
            elif record.type_disengagements == 'pase_servicio_pasivo':
                record.partner_status_especific_historical = record.partner_id.partner_status_especific
                if record.partner_status_especific_reorder == 'passive_reserve_a':
                    record.partner_status_historical = record.partner_id.partner_status
                    record.partner_id.partner_status_especific = record.partner_status_especific_reorder
                    record.state = 'finalized'
                    record.state_finalize = 'hecho'
                    record.partner_id.init_partner()

    @api.onchange('type_disengagements')
    def onchange_type_disengagements(self):
        for record in self:
            if record.type_disengagements == 'fallecimiento':
                record.partner_status_especific_reorder = False

    @api.depends('partner_id')
    def _compute_formatted_name(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.name:
                code_loan_part = " ".join(word.capitalize() for word in
                                          rec.partner_id.category_partner_id.code_loan.split()) if rec.partner_id.category_partner_id and rec.partner_id.category_partner_id.code_loan else ""
                name_part = " ".join(word.capitalize() for word in rec.partner_id.name.split())
                rec.partner_name = f"{code_loan_part} {name_part}".strip()
            else:
                rec.partner_name = ""

    def reconcile_contributions(self, data):
        month = data.get('month')
        year = data.get('year')
        date_field_select = data.get('date_field_select')
        period = f"{month}/{year}"

        filing_cabinet_ids = self.env['nominal.relationship.mindef.contributions'].browse(
            data.get('filing_cabinet_ids', []))
        partner_payroll_ids = self.env['partner.payroll'].browse(data.get('partner_payroll_ids', []))

        filing_map = {rec.eit_item: rec for rec in filing_cabinet_ids}
        reconciled = 0

        for partner in partner_payroll_ids:
            search_partner = filing_map.get(partner.partner_id.code_contact)
            if search_partner:
                reconciled += 1
                search_partner.write({
                    'state': 'reconciled',
                    'date_process': date_field_select,
                    'period_process': period,
                })

        return {
            'message': f'Se conciliaron {reconciled} registros del periodo {period}.'
        }