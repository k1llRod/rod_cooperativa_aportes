from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from itertools import groupby
import numpy as np
import re

# import inflect
# from translate import Translator


class PartnerPayroll(models.Model):
    _name = 'partner.payroll'
    _description = 'Planilla de socio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    state = fields.Selection([('draft', 'Borrador'),
                              ('process', 'En proceso'),
                              ('process_finalized', 'Proceso liquidacion'),
                              ('finalized', 'Liquidado'),
                              ('unassociated','No asociado')],
                             default='draft', track_visibility='always')
    partner_id = fields.Many2one('res.partner', string='Socio')

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
                                                related='partner_id.partner_status_especific', store=True, track_visibility="always")

    partner_status_especific_historical = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Pasivo categoria "A"'),
                                                 ('passive_reserve_b', 'Pasivo categoria "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado historico',
                                                 store=True, track_visibility="always")

    code_contact = fields.Char(string='Código de asociado', related='partner_id.code_contact', store=True)
    vat = fields.Char(string='CI', related='partner_id.vat')
    city = fields.Char(string='Ciudad', related='partner_id.city', store=True)
    date_registration = fields.Datetime(string='Fecha de registro')
    date_burn_partner = fields.Datetime(string='Fecha de afiliacion')
    date_finalized = fields.Datetime(string='Fecha de liquidacion')
    total_contribution = fields.Float(string='Total aportado')
    advanced_payments = fields.Float(string='Tasa regulacion Adelantado')
    payroll_payments_ids = fields.One2many('payroll.payments', 'partner_payroll_id', string='Pagos individuales',
                                           tracking=True)
    capital_initial = fields.Float(string='Capital inicial', compute='compute_contributions', store=True)
    # capital_total = fields.Float(string='Capital total', compute='compute_capital_total')
    # interest_total = fields.Float(string='Interes total', store=True)
    miscellaneous_income = fields.Float(string='Gastos adicional', compute='compute_miscellaneous_income')
    mandatory_contribution_pending = fields.Integer(string='Aportes obligatorios pendientes',
                                                    compute='compute_miscellaneous_income')
    advance_mandatory_certificate = fields.Float(string='Cert. Aport. Oblig. Adelantado')
    total = fields.Float(string='Total', store=True)
    count_pay_contributions = fields.Integer(string='Cantidad de pagos realizados',
                                             compute="compute_count_pay_contributions", store=True)
    advance_regulation_cup = fields.Integer(string='Taza de regulación adelantado',
                                            compute="compute_count_pay_contributions")
    updated_partner = fields.Boolean(string='Actualizado', compute="compute_updated_partner")
    tree_updated_partner = fields.Boolean(string='Actualizado', related='updated_partner')
    outstanding_payments = fields.Integer(string='Pagos pendientes', compute="compute_updated_partner", store=True)

    voluntary_contribution_certificate_total = fields.Float(string='Cert. Aport. Vol. Total',
                                                            compute='compute_count_pay_contributions', store=True)
    mandatory_contribution_certificate_total = fields.Float(string='Cert. Aport. Oblig. total',
                                                            compute='compute_count_pay_contributions', store=True)
    other_contribution_total = fields.Float(string='Otros aportes',
                                            store=True, digits=(16, 2))
    surpluses_total = fields.Float(string='Total excedentes', store=True)
    contribution_total = fields.Float(string='Aporte total', store=True)

    contribution_total_excluded = fields.Float(string='Aporte total excluido', store=True)

    performance_management_total = fields.Float(string='Rendimiento total',
                                                compute='compute_performance_management_total')
    performance_management_ids = fields.One2many('performance.management', 'partner_payroll_id', string='Rendimientos')
    # payroll_payment_ids = fields.One2many('payroll.payment', 'partner_payrolls_id', string='Pagos de planilla')
    advanced_payments_ids = fields.One2many('advance.payments', 'advanced_partner_payroll_id',
                                            string='Pagos adelantados')
    due_payments_ids = fields.One2many('due.payments', 'due_partner_payroll_id', string='Pagos pendientes')
    balance_advance_contribution_passive = fields.Float(string='Saldo aportes pasivos',
                                                        compute='compute_balance_advance')
    balance_advance_regulation_cup = fields.Float(string='Saldo taza de regulación', compute='compute_balance_advance')
    balance_advance_mandatory_contribution = fields.Float(string='Saldo aportes obligatorios',
                                                          compute='compute_balance_advance')
    count_mandatory_contribution_certificate = fields.Integer(string='Contador de certificados de aportes obligatorios',
                                                              compute='compute_contributions')
    journal_id = fields.Many2one('account.journal', string='Diario')
    account_income_id = fields.Many2one('account.account', string='Ingreso', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_income_id'))
    account_inscription_id = fields.Many2one('account.account', string='Inscripcion', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_inscription_id'))
    account_regulation_cup_id = fields.Many2one('account.account', string='Tasa de regulacion', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_regulation_cup_id'))
    account_mandatory_contribution_id = fields.Many2one('account.account', string='Aportes obligatorios', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_mandatory_contribution_id'))
    account_voluntary_contribution_id = fields.Many2one('account.account', string='Aportes voluntarios', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_voluntary_contribution_id'))

    payment_type = fields.Selection([('cossmil_discount', 'Descuento COSSMIL'),
                                     ('voluntary_contribution', 'Aporte voluntario'),
                                     ('voluntary_contribution_discount', 'Descuento devolucion de aportes')], string='Tipo de pago')
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
                              ('external','Externo'),
                              ('rejected', 'Rechazado'),
                              ('unsubscribe', 'Baja'),
                              ('deceased','Fallecido')],
                             string='Estado', default='draft', related='partner_id.state', store=True)


    afiliated_time = fields.Integer(string='Tiempo afiliado', compute='_onchange_name')

    gloss_disengagement = fields.Text(string="Observaciones Baja")
    type_disengagements = fields.Selection([('fallecimiento','Fallecimiento'),
                                           ('retiro_voluntario','Retiro voluntario'),
                                           ('pase_servicio_pasivo','Pase al servicio pasivo')],
                                          string="Baja por", store=True)


    date_unassociated = fields.Date(string='Fecha de no asociado')
    state_finalize = fields.Selection([('borrador','Borrador'),
                                       ('hecho','Hecho')], default='borrador', string='Estado de liquidacion')

    finalize_contributions_ids = fields.One2many('finalize.contributions' , 'partner_payroll_ids', string='Liquidaciones')
    partner_status_especific_reorder = fields.Selection([('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ], string='Tipo de asociado')
    # literal_total_voluntary_contribution = fields.Char(string='Total de certificados de aportes voluntarios', compute='compute_contributions_literal')

    def _compute_total(self):
        for record in self:
            record.total = record.capital_initial + record.voluntary_contribution_certificate_total + record.mandatory_contribution_certificate_total + record.other_contribution_total
    @api.depends('since_payment', 'until_payment')
    def compute_difference_year(self):
        for record in self:
            record.year_now = datetime.now().year
            if record.until_payment != False:
                record.difference_year = record.until_payment.year + 1
                if record.difference_year < record.year_now:
                    record.difference_year = record.year_now
                if record.until_payment.year < 2023:
                    record.difference_year = 2023
            else:
                record.difference_year = 0
    @api.depends('payroll_payments_ids')
    def compute_miscellaneous_income(self):
        self.miscellaneous_income = self.env['ir.config_parameter'].sudo().get_param(
            'rod_cooperativa_aportes.miscellaneous_income')
        for record in self:
            verify = len(record.payroll_payments_ids.filtered(
                lambda x: (x.state == 'transfer' or x.state == 'ministry_defense') and x.miscellaneous_income > 0))
            if verify == 0:
                record.miscellaneous_income = record.env['ir.config_parameter'].sudo().get_param(
                    'rod_cooperativa_aportes.miscellaneous_income')
            else:
                record.miscellaneous_income = 0
            # count_mandatory_contribution = len(record.payroll_payments_ids.filtered())
            periods = self.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.month_ids')
            mandatory_contribution = float(record.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.mandatory_contribution_certificate'))
            year_now = datetime.now().year
            filter_periods = re.findall(r'\d+', periods)
            count_periods = len(filter_periods)
            count_mandatory_contributions = count_periods * mandatory_contribution
            verificate_payments = record.payroll_payments_ids.filtered(
                lambda x: (x.state == 'transfer' or x.state == 'ministry_defense') and x.payment_date.year == year_now)
            sum_verificate_payments = sum(verificate_payments.mapped('mandatory_contribution_certificate'))
            record.mandatory_contribution_pending = count_mandatory_contributions - sum_verificate_payments

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('partner.payroll')
        vals['name'] = name
        res = super(PartnerPayroll, self).create(vals)
        return res

    # def write(self, vals):
    #     res = super(PartnerPayroll, self).write(vals)
    #     self.compute_count_pay_contributions()
    #     return res

    @api.depends('payroll_payments_ids')
    def compute_contributions(self):
        for record in self:
            record.voluntary_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(
                lambda x: (x.state == 'transfer' or x.state == 'ministry_defense')).mapped(
                'voluntary_contribution_certificate'))
            record.count_mandatory_contribution_certificate = len(
                record.payroll_payments_ids.filtered(lambda x: x.mandatory_contribution_certificate > 0))
            record.capital_initial = sum(
                record.payroll_payments_ids.filtered(lambda x: x.state == 'contribution_interest' or x.state == 'capital_initial').mapped(
                    'voluntary_contribution_certificate'))


    def init_payroll_partner_wizard(self):
        # Acción para abrir el wizard
        # Puedes personalizar esta función según tus necesidades
        record_id = self.id
        context = {
            'default_partner_payroll_id': record_id,
            'default_capital_base': self.capital_base,
        }
        return {
            'name': 'Conciliar pagos de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'init.payroll.partner',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }

    def import_payroll(self):
        return {
            'name': 'Conciliar pagos de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'reconcile.contributions',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

    @api.depends('partner_id')
    def compute_partner_status(self):
        for record in self:
            record.partner_status = record.partner_id.status

    def wizard_pay_contribution(self):
        # Acción para abrir el wizard
        # Puedes personalizar esta función según tus necesidades
        record_id = self.id
        context = {
            'default_partner_payroll_id': record_id,
            'default_capital_base': self.capital_base,
        }
        return {
            'name': 'Conciliar pagos de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'pay.contribution',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }

    @api.depends('payroll_payments_ids')
    def compute_count_pay_contributions(self):
        for record in self:
            record.count_pay_contributions = len(record.payroll_payments_ids.filtered(lambda x: x.state != 'draft'))
            record.mandatory_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(
                lambda x: x.state == 'transfer' or x.state == 'ministry_defense').mapped(
                'mandatory_contribution_certificate'))
            record.voluntary_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(
                lambda x: x.state == 'transfer' or x.state == 'ministry_defense').mapped(
                'voluntary_contribution_certificate'))
            interest_total = sum(record.performance_management_ids.mapped('yield_amount'))
            record.other_contribution_total = sum(round(c,2)for c in record.payroll_payments_ids.filtered(lambda x: x.state == 'other_contribution').mapped('other_contribution'))
            record.surpluses_total = sum(
                record.payroll_payments_ids.filtered(lambda x: x.state == 'surpluses').mapped(
                    'other_contribution'))
            record.contribution_total = record.voluntary_contribution_certificate_total + record.mandatory_contribution_certificate_total + interest_total + record.capital_initial + record.other_contribution_total

    def return_draft(self):
        self.state = 'draft'
        # if self.state == 'process' and self.count_pay_contributions == 0:
        #     self.state = 'draft'
        # else:
        #     raise ValidationError(_('No se puede regresar a borrador si ya se han realizado pagos'))

    @api.depends('payroll_payments_ids')
    def compute_updated_partner(self):
        regulation_cup = float(self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.regulation_cup'))
        mandatory_contribution = float(self.env['ir.config_parameter'].sudo().get_param(
            'rod_cooperativa_aportes.mandatory_contribution_certificate'))
        diff_months = 0
        count_payments = 0
        for record in self:
            if record.date_burn_partner:
                if record.partner_status_especific == 'passive_reserve_a' or record.partner_status_especific == 'passive_reserve_b':
                    # record.due_payments_ids.unlink()
                    self.env['due.payments'].search([('due_partner_payroll_id', '=', record.id)]).unlink()
                    gestion_ini = 0
                    if record.since_payment != False:
                        if record.since_payment.year > 2023:
                            gestion_ini = record.since_payment.year
                        else:
                            gestion_ini = 2023
                    gestion_end = datetime.now().year
                    n = gestion_end - gestion_ini + 1
                    gestion_process = gestion_ini
                    inscription = 10
                    reg_cup = regulation_cup * 12
                    mandatory = mandatory_contribution * 2
                    post_mortem = 167.28
                    period_reg = []
                    sw = 0
                    for i in range(n):
                        try:
                            periods = record.payroll_payments_ids.filtered(lambda x:x.period_register).mapped('period_register')
                            period_reg = np.unique(periods)
                            if i < len(period_reg):
                                period = period_reg[i]
                            else:
                                period = False
                            register = record.payroll_payments_ids.filtered(lambda x: x.period_register == period)
                            sum_miscellanous = sum(register.mapped('miscellaneous_income'))
                            sum_regulation_cup = sum(register.mapped('regulation_cup'))
                            sum_mandatory = sum(register.mapped('mandatory_contribution_certificate'))
                            sum_voluntary = sum(register.mapped('voluntary_contribution_certificate'))
                            cal_regulation_cup = reg_cup - sum_regulation_cup
                            cal_mandatory = mandatory - sum_mandatory
                            if sw == 0:
                                cal_miscellaneous = 0 if record.miscellaneous_income == 0 else inscription - sum_miscellanous
                                sw = 1
                            else:
                                cal_miscellaneous = 0

                            cal_post_mortem = 0 if gestion_process <= record.until_payment.year else post_mortem - sum_voluntary
                            d_total = cal_miscellaneous + cal_regulation_cup + cal_mandatory + cal_post_mortem
                            # record.due_payments_ids.unlink()
                            self.env['due.payments'].create({
                                'name': period if len(period_reg) > 0 else 0,
                                'd_miscellaneous_income': cal_miscellaneous,
                                'd_regulation_cup': cal_regulation_cup,
                                'd_mandatory_contribution': cal_mandatory,
                                'd_voluntary_contribution': sum_voluntary,
                                'd_post_mortem': cal_post_mortem,
                                'd_total': d_total,
                                'due_partner_payroll_id': record.id,
                                'gestion': gestion_process
                            })
                            gestion_process += 1
                            count_payments = 0
                            d_total = 0
                        except:
                            count_payments = 0
                            d_total = 0
                            pass

                else:
                    diff = relativedelta(datetime.now(), record.date_burn_partner)
                    diff_months = diff.years * 12 + diff.months
                    count_payments = len(
                        record.payroll_payments_ids.filtered(
                            lambda x: (x.state == 'ministry_defense' or x.state == 'transfer') and x.drawback == False))
            if count_payments >= diff_months and record.state != 'draft':
                record.updated_partner = True
                self.env.user.notify_success(message='Planilla de aportes actualizado'.format(record.partner_id.name),
                                             title='Verificado')
                record.outstanding_payments = 0
                record.must_regulation_rate = 0
                record.must_mandatory_contribution = 0
            else:
                record.updated_partner = False
                record.outstanding_payments = diff_months - count_payments
                record.must_regulation_rate = record.outstanding_payments * regulation_cup
                record.must_mandatory_contribution = (record.outstanding_payments/6) * mandatory_contribution
                record.must_gestion = count_payments / 12
                record.must_total = record.must_regulation_rate + record.must_mandatory_contribution + record.must_post_mortem
                self.env.user.notify_warning(
                    message='Planilla de aportes desactualizada'.format(record.partner_id.name))

    def print_report_total(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("2-Factor authentication is now enabled."),
                'sticky': False,
            }
        }

    # @api.depends('payroll_payments_ids')
    # def compute_outstanding_payments(self):
    #     for record in self:
    #         if record.date_burn_partner != False:
    #             make_register = round(((datetime.now() - record.date_burn_partner).days) / 30) - 1
    #         else:
    #             make_register = 0
    #         # make_register = record.calculate_month_difference()
    #         record.outstanding_payments = make_register - round(len(record.payroll_payments_ids.filtered(lambda x: (x.state == 'transfer' or x.state == 'ministry_defense') and x.drawback == False)))


    def calculate_month_difference(self):
        for record in self:
            if record.date_burn_partner:
                diff = relativedelta(datetime.now(), record.date_burn_partner)
                diff_months = diff.years * 12 + diff.months
            else:
                diff_months = 0
        return diff_months

    def select_init_partner_payroll(self):
        for record in self:
            if record.partner_status == 'active' and record.state == 'draft':
                if record.date_burn_partner == False:
                    record.date_burn_partner = datetime.now()
                else:
                    record.state = 'process'

    def validate_partner_passive(self):
        for record in self:
            record.state = 'process'

    def init_partner_payroll_interest(self):
        # wizard = self.env['set.interes'].create({'partner_payroll_id': self.id})
        for record in self:
            context = {
                'default_partner_payroll_id': record.id,
            }
            return {
                'name': 'Establecer interes de aportes',
                'type': 'ir.actions.act_window',
                'res_model': 'set.interes',
                'view_mode': 'form',
                'view_type': 'form',
                'context': context,
                'target': 'new',
            }

    def assign_performance(self):
        performance_index_log = self.env['performance_index.log'].search([('state', '=', 'validate')])
        return {
            'name': 'Establecer interes de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'set.management',
            'view_mode': 'form',
            'view_type': 'form',
            # 'context': context,
            'target': 'new',
        }

    def resume_process(self):
        for record in self:
            if record.date_burn_partner != False:
                record.state = 'process'

    @api.depends('performance_management_ids')
    def compute_performance_management_total(self):
        for record in self:
            record.performance_management_total = sum(record.performance_management_ids.mapped('yield_amount'))

    def compute_balance_advance(self):
        for record in self:
            record.balance_advance = record.contribution_total - record.performance_management_total


    def finalized_payroll(self):
        total_contributions = (self.capital_initial + self.voluntary_contribution_certificate_total +
                               self.mandatory_contribution_certificate_total + self.performance_management_total + self.other_contribution_total + self.surpluses_total)

        loan_id = self.env['loan.application'].search([('partner_id','=',self.partner_id.id),('state','=','progress')])
        total_loan_capital_bolivianos = loan_id.balance_capital * loan_id.value_dolar
        total_balance_total_interest_month_bolivianos = loan_id.balance_total_interest_month * loan_id.value_dolar
        context = {
            'default_partner_payroll_id': self.id,
            # 'default_capital_initial': self.capital_initial,
            'default_total_mandatory_contributions_certificate': self.mandatory_contribution_certificate_total,
            'default_total_voluntary_contributions_certificate': self.voluntary_contribution_certificate_total,
            'default_total_performance_contributions': self.performance_management_total,
            'default_total_other_contributions': self.other_contribution_total,
            'default_total_balance_capital': self.contribution_total,
            'default_capital_initial': self.capital_initial,
            'default_total_contributions': total_contributions,
            'default_total_surpluses': self.surpluses_total,
            'default_loan_application_id': loan_id.id,
            'default_total_loan_capital': loan_id.balance_capital,
            'default_total_balance_total_interest_month': loan_id.balance_total_interest_month,
            'default_default_dolar': loan_id.value_dolar,
            'default_total_loan_capital_bolivianos': total_loan_capital_bolivianos,
            'default_total_balance_total_interest_month_bolivianos': total_balance_total_interest_month_bolivianos,

        }
        return {
            'name': 'Formulario de liquidacion',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.finalized.contributions',
            'view_mode': 'form',
            'view_type': 'form',
            'context': context,
            'target': 'new',
        }

    # def cron_compute_outstanding_payments(self):
    #     for record in self:
    #         record.compute_outstanding_payments()

    def publish_accouting_entries(self):
        for record in self:
            payments = record.payroll_payments_ids
            for payment in payments:
                income = record.account_income_id
                inscription = record.account_inscription_id
                regulation_cup = record.account_regulation_cup_id
                mandatory_contribution = record.account_mandatory_contribution_id
                voluntary_contribution = record.account_voluntary_contribution_id
                payment.create_account_move(income,inscription,regulation_cup,mandatory_contribution,voluntary_contribution)

    def _init_report_partner_payroll(self):
        self_obj = self.browse(self)[0]
        data_obj = self.pool.get('ir.model.data')
        data_id = data_obj._get_id('rod_cooperativa_aportes', 'partner_payroll_tree_id')
        view_id = False
        if data_id:
            view_id = data_obj.browse(data_id).res_id
        form_data_id = data_obj._get_id('rod_cooperativa_aportes', 'partner_payroll_form_id')
        if form_data_id:
            form_view_id = data_obj.browse(form_data_id).res_id

        # context.update({'active_ids': [], 'no_complete_name':1})
        return {
            'name': _('Planilla de socio'),
            'view_type': 'form',
            'res_model': 'partner.payroll',
            'view_id': False,
            'views': [(view_id, 'tree'), (form_view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'nodestroy': True,
            # 'context': context,
        }

    def wizard_payroll_return(self):
        for record in self:
            context = {
                'default_name': record.name,
                'default_date_pivote': datetime.now(),
                'default_payment_date': datetime.now(),
                'default_mount': record.total,
                'default_glosa': 'Devolucion de aportes',
                'default_partner_payroll_id': record.id,
            }
            return {
                'name': 'Pago de aportes',
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.payroll.return',
                'view_mode': 'form',
                'view_type': 'form',
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
        for record in self:
            total = round(sum(record.payroll_payments_ids.filtered(lambda x: x.state == 'ministry_defense').mapped('income')),2)
        context = {
            'default_partner_payroll_id': self.id,
            'default_total_contributions': total,
        }
        return {
            'name': 'Pago de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.unassociated',
            'view_mode': 'form',
            'view_type': 'form',
            'context': context,
            'target': 'new',
        }

    def updated_contributions(self):
        rows = self.payroll_payments_ids.filtered(lambda x:x.state == 'other_contribution' or x.state == 'surpluses')
        for record in rows:
            record.other_contribution = record.income
            record.income = 0
            record.regulation_cup = 0
            record.miscellaneous_income = 0
            record.mandatory_contribution_certificate = 0

    def process_partner_status(self):
        for record in self:
            if record.state == 'process':
                raise ValidationError(_('La planilla de aportes debe estar en un estaod "PROCESO DE LIQUIDACION"'))
            if record.type_disengagements == 'fallecimiento':
                record.partner_id.state = 'deceased'
                record.state = 'finalized'
                record.partner_id.glosa = record.gloss_disengagement
                record.partner_id.date_deceased = datetime.now()
                record.state_finalize = 'hecho'
            if record.type_disengagements == 'retiro_voluntario':
                record.partner_id.state = 'unsubscribe'
                record.state = 'finalized'
                record.state_finalize = 'hecho'
            if record.type_disengagements == 'pase_servicio_pasivo':
                record.partner_status_especific_historical = record.partner_id.partner_status_especific
                if record.partner_status_especific_reorder == 'passive_reserve_a':
                    record.partner_status_especific_historical = record.partner_id.partner_status_especific
                    record.partner_status_historical = record.partner_id.partner_status
                    record.partner_id.partner_status_especific = record.partner_status_especific_reorder
                    record.state = 'finalized'
                    record.state_finalize = 'hecho'
                    record.partner_id.init_partner()

    @api.onchange('type_disengagements')
    def onchange_type_disengagements(self):
        for record in self:
            if record.type_disengagements == 'fallecimiento':
                record.partner_status_especific_reorder = ''






