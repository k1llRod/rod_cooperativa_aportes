from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class PartnerPayroll(models.Model):
    _name = 'partner.payroll'
    _description = 'Planilla de socio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    state = fields.Selection([('draft', 'Borrador'), ('process', 'En proceso'), ('finalized', 'Liquidado')],
                             default='draft')
    partner_id = fields.Many2one('res.partner', string='Socio')

    partner_status = fields.Selection([('activate', 'Servicio activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive_reserve_a', 'Reserva pasivo "A"'),
                                       ('passive_reserve_b', 'Reserva pasivo "B"')],
                                      string='Situación de socio', related='partner_id.partner_status', readonly=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Situación de socio',
                                                related='partner_id.partner_status_especific', readonly=True)

    date_registration = fields.Datetime(string='Fecha de registro')
    date_burn_partner = fields.Datetime(string='Fecha de afiliacion')
    total_contribution = fields.Float(string='Total aportado')
    advanced_payments = fields.Float(string='Pagos adelantados', compute="compute_advanced_payments")
    payroll_payments_ids = fields.One2many('payroll.payments', 'partner_payroll_id', string='Pagos individuales',
                                           tracking=True)
    # capital_base = fields.Float(string='Capital base', store=True, tracking=True)
    # capital_total = fields.Float(string='Capital total', compute='compute_capital_total')
    # interest_total = fields.Float(string='Interes total', store=True)
    miscellaneous_income = fields.Float(string='Gastos adicional', compute="compute_miscellaneous_income", store=True)
    total = fields.Float(string='Total', store=True)
    count_pay_contributions = fields.Integer(string='Cantidad de pagos realizados', compute="compute_count_pay_contributions")
    advance_regulation_cup = fields.Integer(string='Taza de regulación adelantado',
                                            compute="compute_count_pay_contributions")
    updated_partner = fields.Boolean(string='Actualizado', compute="compute_updated_partner")
    tree_updated_partner = fields.Boolean(string='Actualizado', related='updated_partner')
    outstanding_payments = fields.Integer(string='Pagos pendientes', compute="compute_outstanding_payments")

    voluntary_contribution_certificate_total = fields.Float(string='Ingreso total', compute="compute_voluntary_contribution_certificate_total", store=True)
    mandatory_contribution_certificate_total = fields.Float(string='Aporte voluntario total', compute="compute_mandatory_contribution_certificate_total", store=True)
    contribution_total = fields.Float(string='Aporte total', compute="compute_contribution_total", store=True)
    performance_management_ids = fields.One2many('performance.management', 'partner_payroll_id', string='Rendimientos')

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('partner.payroll')
        vals['name'] = name
        res = super(PartnerPayroll, self).create(vals)
        return res

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

    @api.depends('payroll_payments_ids')
    def compute_voluntary_contribution_certificate_total(self):
        for record in self:
            record.voluntary_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(lambda x: x.state != 'draft').mapped(
                                    'voluntary_contribution_certificate'))
            record.mandatory_contribution_certificate_total = sum(record.payroll_payments_ids.filtered(lambda x: x.state != 'draft').mapped(
                                    'mandatory_contribution_certificate'))


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

    # @api.depends('payroll_payments_ids')
    def compute_miscellaneous_income(self):
        miscellaneous_income = float(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.miscellaneous_income'))
        for record in self:
            if record.state != 'draft':
                if record.payroll_payments_ids.filtered(lambda x: x.miscellaneous_income == miscellaneous_income and (
                        x.state == 'ministry_defense' or x.state == 'transfer')):
                    record.miscellaneous_income = miscellaneous_income - float(
                        record.payroll_payments_ids.mapped('miscellaneous_income')[0])
                else:
                    record.miscellaneous_income = miscellaneous_income
            else:
                record.miscellaneous_income = miscellaneous_income

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

    def return_draft(self):
        if self.state == 'process' and self.count_pay_contributions == 0:
            self.state = 'draft'
        else:
            raise ValidationError(_('No se puede regresar a borrador si ya se han realizado pagos'))

    @api.depends('payroll_payments_ids')
    def compute_advanced_payments(self):
        for record in self:
            total_normal = record.count_pay_contributions * 0.50
            total_payments = sum(record.payroll_payments_ids.mapped('regulation_cup'))
            record.advanced_payments = total_payments - total_normal
    # @api.depends('payroll_payments_ids')
    # def compute_advance_regulation_cup(self):

    @api.depends('payroll_payments_ids')
    def compute_updated_partner(self):
        diff_months = 0
        for record in self:
            if record.date_burn_partner:
                diff = relativedelta(datetime.now(), record.date_burn_partner)
                diff_months = diff.years * 12 + diff.months
            count_payments = len(record.payroll_payments_ids.filtered(lambda x: x.state == 'ministry_defense' or x.state == 'transfer'))
            if count_payments >= diff_months and record.state != 'draft':
                record.updated_partner = True
                self.env.user.notify_success(message='Planilla de aportes actualizado'.format(record.partner_id.name),title='Verificado')
            else:
                record.updated_partner = False
                self.env.user.notify_warning(message='Planilla de aportes desactualizada'.format(record.partner_id.name))


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

    def compute_outstanding_payments(self):
        for record in self:
            if record.date_burn_partner != False:
                make_register = int(((datetime.now() - record.date_burn_partner).days) / 30)
            else:
                make_register = 0
            # make_register = record.calculate_month_difference()
            record.outstanding_payments = make_register - int(len(record.payroll_payments_ids.filtered(lambda x: x.state != 'draft' and x.drawback == False)))

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
                # make_register = record.calculate_month_difference()
                # date = record.date_burn_partner
                # for i in range(make_register):
                #     record.payroll_payments_ids = [(0, 0, {'payment_date': date,
                #                                            'income': 0,
                #                                            'state': 'draft',
                #                                            })]
                #     date = date + relativedelta(months=1)
    def compute_contribution_total(self):
        for record in self:
            record.contribution_total = record.voluntary_contribution_certificate_total + record.mandatory_contribution_certificate_total


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
        performance_index_log = self.env['performance_index.log'].search([('state','=','validate')])
        return {
            'name': 'Establecer interes de aportes',
            'type': 'ir.actions.act_window',
            'res_model': 'set.management',
            'view_mode': 'form',
            'view_type': 'form',
            # 'context': context,
            'target': 'new',
        }




