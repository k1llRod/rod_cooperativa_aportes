from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import re


# import inflect
# from translate import Translator


class PartnerPayroll(models.Model):
    _name = 'partner.payroll'
    _description = 'Planilla de socio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    state = fields.Selection([('draft', 'Borrador'), ('process', 'En proceso'), ('finalized', 'Liquidado')],
                             default='draft')
    partner_id = fields.Many2one('res.partner', string='Socio')

    partner_status = fields.Selection([('active', 'Activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive', 'Servicio pasivo'),
                                       ('leave', 'Baja')], string="Situacion general",
                                      related='partner_id.partner_status', store=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado',
                                                related='partner_id.partner_status_especific', store=True)
    code_contact = fields.Char(string='Código de asociado', related='partner_id.code_contact', store=True)
    vat = fields.Char(string='CI', related='partner_id.vat')
    date_registration = fields.Datetime(string='Fecha de registro')
    date_burn_partner = fields.Datetime(string='Fecha de afiliacion')
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
    outstanding_payments = fields.Integer(string='Pagos pendientes', compute="compute_outstanding_payments", store=True)

    voluntary_contribution_certificate_total = fields.Float(string='Cert. Aport. Vol. Total',
                                                            compute='compute_count_pay_contributions', store=True)
    mandatory_contribution_certificate_total = fields.Float(string='Cert. Aport. Oblig. total',
                                                            compute='compute_count_pay_contributions', store=True)
    contribution_total = fields.Float(string='Aporte total', store=True)
    performance_management_total = fields.Float(string='Rendimiento total',
                                                compute='compute_performance_management_total')
    performance_management_ids = fields.One2many('performance.management', 'partner_payroll_id', string='Rendimientos')
    # payroll_payment_ids = fields.One2many('payroll.payment', 'partner_payrolls_id', string='Pagos de planilla')
    advanced_payments_ids = fields.One2many('advance.payments', 'advanced_partner_payroll_id',
                                            string='Pagos adelantados')
    balance_advance_contribution_passive = fields.Float(string='Saldo aportes pasivos',
                                                        compute='compute_balance_advance')
    balance_advance_regulation_cup = fields.Float(string='Saldo taza de regulación', compute='compute_balance_advance')
    balance_advance_mandatory_contribution = fields.Float(string='Saldo aportes obligatorios',
                                                          compute='compute_balance_advance')
    count_mandatory_contribution_certificate = fields.Integer(string='Contador de certificados de aportes obligatorios',
                                                              compute='compute_contributions')
    account_income_id = fields.Many2one('account.account', string='Ingreso', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_income_id'))
    account_inscription_id = fields.Many2one('account.account', string='Inscripcion', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_inscription_id'))
    account_regulation_cup_id = fields.Many2one('account.account', string='Tasa de regulacion', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_regulation_cup_id'))
    account_mandatory_contribution_id = fields.Many2one('account.account', string='Aportes obligatorios', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_mandatory_contribution_id'))
    account_voluntary_contribution_id = fields.Many2one('account.account', string='Aportes voluntarios', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.account_voluntary_contribution_id'))

    # literal_total_voluntary_contribution = fields.Char(string='Total de certificados de aportes voluntarios', compute='compute_contributions_literal')

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

    @api.depends('payroll_payments_ids')
    def compute_contributions(self):
        for record in self:
            record.voluntary_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(
                lambda x: (x.state == 'transfer' or x.state == 'ministry_defense')).mapped(
                'voluntary_contribution_certificate'))
            record.count_mandatory_contribution_certificate = len(
                record.payroll_payments_ids.filtered(lambda x: x.mandatory_contribution_certificate > 0))
            record.capital_initial = sum(
                record.payroll_payments_ids.filtered(lambda x: x.state == 'contribution_interest').mapped(
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
            record.contribution_total = record.voluntary_contribution_certificate_total + record.mandatory_contribution_certificate_total + interest_total + record.capital_initial

    def return_draft(self):
        self.state = 'draft'
        # if self.state == 'process' and self.count_pay_contributions == 0:
        #     self.state = 'draft'
        # else:
        #     raise ValidationError(_('No se puede regresar a borrador si ya se han realizado pagos'))

    @api.depends('payroll_payments_ids')
    def compute_updated_partner(self):
        diff_months = 0
        for record in self:
            if record.date_burn_partner:
                diff = relativedelta(datetime.now(), record.date_burn_partner)
                diff_months = diff.years * 12 + diff.months
            count_payments = len(
                record.payroll_payments_ids.filtered(
                    lambda x: (x.state == 'ministry_defense' or x.state == 'transfer') and x.drawback == False))
            if count_payments >= diff_months and record.state != 'draft':
                record.updated_partner = True
                self.env.user.notify_success(message='Planilla de aportes actualizado'.format(record.partner_id.name),
                                             title='Verificado')
            else:
                record.updated_partner = False
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

    @api.depends('payroll_payments_ids')
    def compute_outstanding_payments(self):
        for record in self:
            if record.date_burn_partner != False:
                make_register = round(((datetime.now() - record.date_burn_partner).days) / 30)
            else:
                make_register = 0
            # make_register = record.calculate_month_difference()
            record.outstanding_payments = make_register - round(len(record.payroll_payments_ids.filtered(lambda x: (x.state == 'transfer' or x.state == 'ministry_defense') and x.drawback == False)))


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
        for record in self:
            record.state = 'finalized'

    def cron_compute_outstanding_payments(self):
        for record in self:
            record.compute_outstanding_payments()

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