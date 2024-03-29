from xml import etree

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re


class PayrollPayments(models.Model):
    _name = 'payroll.payments'
    _description = 'Pagos individuales de planilla'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='ID aporte')
    partner_payroll_id = fields.Many2one('partner.payroll', string='Planilla de socio')
    partner_name = fields.Char(String='Nombre del socio', related='partner_payroll_id.partner_id.name', store=True)
    partner_code_contact = fields.Char(string='Codigo de socio', related='partner_payroll_id.partner_id.code_contact', store=True)
    partner_status = fields.Selection([('active', 'Activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive', 'Servicio pasivo'),
                                       ('leave', 'Baja')], string="Situacion general",
                                      related='partner_payroll_id.partner_id.partner_status', store=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado',
                                                related='partner_payroll_id.partner_id.partner_status_especific', store=True)

    income = fields.Float(string='DESC. MINDEF', required=True, tracking=True)
    income_passive = fields.Float(string='DESC. PASIVO', required=True, tracking=True)
    mandatory_contribution_certificate = fields.Float(string='CERT. APOR. OBLI.', default=0.0)
    voluntary_contribution_certificate = fields.Float(string='CERT. APOR. VOL.',
                                                      compute="compute_voluntary_contribution_certificate", store=True)
    regulation_cup = fields.Float(string='TASA REGULACION', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.regulation_cup')))
    payment_post_mortem = fields.Float(string='PAGO POST MORTEM')
    miscellaneous_income = fields.Float(string='INSCRIPCION')
    payment_date = fields.Datetime(string='Fecha de pago', default=fields.Datetime.now(), required=True, tracking=True)
    period_register = fields.Char(string='Periodo de registro', compute="compute_period_register", store=True)
    state = fields.Selection(
        [('draft', 'Borrador'), ('transfer', 'Transferencia bancaria'), ('ministry_defense', 'Ministerio de defensa'), ('contribution_interest', 'Aporte y rendimiento COAA')],
        default='draft', tracking=True)
    capital = fields.Float(string='Capital')
    interest = fields.Float(string='Interes')
    drawback = fields.Boolean(string='Reintegro')
    switch_draf = fields.Boolean(string='Switch draft')
    historical_contribution_coaa = fields.Float(string='Aporte historico COAA')
    historical_interest_coaa = fields.Float(string='Rendimiento historico COAA')
    glosa_contribution_interest = fields.Text(string='Glosa de aporte')
    advanced_automata = fields.Boolean(string='Adelanto automatico')
    register_advanced_payments_ids = fields.Many2one('advance.payments')

    # @api.depends('partner_payroll_id')
    # def _get_partner_name(self):
    #     for record in self:
    #         record.partner_name = record.partner_payroll_id.partner_id.name
    #         record.partner_code_contact = record.partner_payroll_id.partner_id.code_contact
    #         # record.partner_status_especific = record.partner_payroll_id.partner_status_especific
    #         record.partner_status = record.partner_payroll_id.partner_status


    @api.depends('payment_date')
    def compute_period_register(self):
        for record in self:
            record.period_register = record.payment_date.strftime('%m') + '/' + record.payment_date.strftime('%Y')

    @api.model
    def create(self, vals_list):
        name = self.env['ir.sequence'].next_by_code('payroll.payments')
        vals_list['name'] = name
        res = super(PayrollPayments, self).create(vals_list)
        # if len(res.partner_payroll_id.payroll_payments_ids) == 1:
        #     res.partner_payroll_id.date_burn_partner = fields.Datetime.now()
        #     if res.partner_payroll_id.partner_status_especific == 'active_service' or res.partner_payroll_id.partner_status_especific == 'letter_a' or res.partner_payroll_id.partner_status_especific == 'passive_reserve_b':
        #         res.partner_payroll_id.state = 'process'
        res.partner_payroll_id.message_post(body="Pago creado: " + vals_list['name'])
        return res

    def open_one2many_line(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Model Title',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
        }

    @api.depends('income', 'income_passive', 'mandatory_contribution_certificate', 'miscellaneous_income',
                 'regulation_cup','historical_contribution_coaa','historical_interest_coaa')
    def compute_voluntary_contribution_certificate(self):
        for record in self:
            if record.partner_payroll_id.partner_status == 'active':
                record.voluntary_contribution_certificate = record.income - record.mandatory_contribution_certificate - record.miscellaneous_income - record.regulation_cup
                if record.state == 'contribution_interest':
                    record.regulation_cup = 0
                    record.miscellaneous_income = 0
                    record.mandatory_contribution_certificate = 0
                    record.voluntary_contribution_certificate = record.historical_contribution_coaa + record.historical_interest_coaa
            else:
                record.voluntary_contribution_certificate = record.income_passive - record.mandatory_contribution_certificate - record.miscellaneous_income - record.regulation_cup

    def confirm_payroll(self):
        for record in self:
            if record.state == 'draft':
                if record.income < 0:
                    raise ValidationError('El ingreso no puede ser menor o igual a cero')
                if record.partner_payroll_id.date_burn_partner == False:
                    record.partner_payroll_id.date_burn_partner = record.payment_date
                    record.partner_payroll_id.state = 'process'
                verify = record.partner_payroll_id.payroll_payments_ids.filtered(
                    lambda x: (x.state == 'transfer' or x.state == 'ministry_defense') and (
                            x.period_register == record.period_register))
                if len(verify) > 0 and record.drawback == False:
                    raise ValidationError('Ya existe un pago confirmado para este periodo')
                if record.partner_payroll_id.advance_mandatory_certificate > 0 and record.switch_draf == False:
                    record.partner_payroll_id.advance_mandatory_certificate = record.partner_payroll_id.advance_mandatory_certificate - record.mandatory_contribution_certificate
                    if record.partner_payroll_id.advanced_payments > 0:
                        record.partner_payroll_id.advanced_payments = record.partner_payroll_id.advanced_payments - record.regulation_cup
                # else:
                #     record.switch_draf = False
                record.write({'state': 'transfer'})
                record.partner_payroll_id.compute_count_pay_contributions()

    def return_draft(self):
        self.state = 'draft'
        self.switch_draf = False

    def extract_numbers(self, text):
        numbers = re.findall(r'\d+', text)
        return [int(number) for number in numbers]

    @api.onchange('income', 'onchange', 'payment_date')
    def onchange_income(self):
        verify_miscellaneous_income = self.partner_payroll_id.miscellaneous_income
        if verify_miscellaneous_income == 0:
            self.miscellaneous_income = 0
        else:
            self.miscellaneous_income = self.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.miscellaneous_income')
        verify_certify = len(self.partner_payroll_id.payroll_payments_ids.filtered(
            lambda x: x.mandatory_contribution_certificate > 0 and x.state != 'draft'))
        if verify_certify == 0:
            self.mandatory_contribution_certificate = 100
            return

        month_flag = self.extract_numbers(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.month_ids'))
        sw = 0
        for month in month_flag:
            if month == self.payment_date.month and self.drawback == False:
                self.mandatory_contribution_certificate = 100
                sw = 1
        if sw == 0:
            self.mandatory_contribution_certificate = 0

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError('No se puede eliminar un pago que ya ha sido confirmado')
        return super(PayrollPayments, self).unlink()

    def ministry_defense(self):
        for record in self:
            if record.state == 'draft':
                if record.income < 0:
                    raise ValidationError('El ingreso no puede ser menor o igual a cero')
                if record.partner_payroll_id.date_burn_partner == False:
                    record.partner_payroll_id.date_burn_partner = record.payment_date
                    record.partner_payroll_id.state = 'process'
                verify = record.partner_payroll_id.payroll_payments_ids.filtered(
                    lambda x: (x.state == 'ministry_defense' and x.period_register == record.period_register))
                if len(verify) > 0 and record.drawback == False:
                    raise ValidationError('Ya existe un pago confirmado para este periodo')
                if record.partner_payroll_id.advance_mandatory_certificate > 0 and record.switch_draf == False:
                    record.partner_payroll_id.advance_mandatory_certificate = record.partner_payroll_id.advance_mandatory_certificate - record.mandatory_contribution_certificate
                    if record.partner_payroll_id.advanced_payments > 0:
                        record.partner_payroll_id.advanced_payments = record.partner_payroll_id.advanced_payments - record.regulation_cup
                else:
                    record.switch_draf = False
                record.write({'state': 'ministry_defense'})
                record.partner_payroll_id.compute_count_pay_contributions()

    # def write(self, vals):
    #     a = 1
    #     res = super(PayrollPayments, self).write(vals)
    #     return res

    @api.onchange('drawback')
    def onchange_drawback(self):
        for record in self:
            record.mandatory_contribution_certificate = 0
            record.regulation_cup = 0
            record.onchange_income()

    def generate_certificate_report(self):
        certificate = self.env['report.payment.payroll'].browse(self.id)
        if certificate:
            report = self.env.ref('certificate.report_certificate')
            return report.report_action(certificate)

    # def drawback(self):
    #     for record in self:
    #         if record.state == 'draft':
    #             if record.income < 0:
    #                 raise ValidationError('El reintegro no puede ser menor o igual a cero')
    #             verify = record.partner_payroll_id.payroll_payments_ids.filtered(
    #                 lambda x: (x.state == 'transfer' or x.state == 'ministry_defense') and (x.period_register == record.period_register))
    #             if len(verify) > 0:
    #                 record.state = 'drawback'
    #             else:
    #                 raise ValidationError('El reintegro no tiene un periodo para completar el pago')

    def _payments_reports(self):
        view_id = self.env.ref('rod_cooperativa_aportes.payroll_payments_tree_id').id
        search_id = self.env.ref('rod_cooperativa_aportes.view_payroll_payments_filter').id
        return {
            'name': 'Detalle de aportes',
            'res_model': 'payroll.payments',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'tree',
            'search_view_id': search_id,
            'domain': [],
        }

    def contribution_interest(self):
        for record in self:
            if record.partner_payroll_id.date_burn_partner == False:
                record.partner_payroll_id.date_burn_partner = record.payment_date
                record.partner_payroll_id.state = 'process'
            record.state = 'contribution_interest'
            record.switch_draf = True

    def draft_massive(self):
        for record in self:
            record.state = 'draft'