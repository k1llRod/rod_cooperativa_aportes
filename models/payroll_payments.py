from xml import etree

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re


class PayrollPayments(models.Model):
    _name = 'payroll.payments'
    _description = 'Pagos individuales de planilla'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre')
    partner_payroll_id = fields.Many2one('partner.payroll', string='Planilla de socio')
    partner_name = fields.Char(String='Nombre del socio', related='partner_payroll_id.partner_id.name')
    income = fields.Float(string='Ingresos', required=True, tracking=True)
    mandatory_contribution_certificate = fields.Float(string='Cert. Apor.', default=0.0)
    voluntary_contribution_certificate = fields.Float(string='Total mensual',
                                                      compute="compute_voluntary_contribution_certificate", store=True)
    regulation_cup = fields.Float(string='Tasa Regulación')
    miscellaneous_income = fields.Float(string='Inscripcion', default=lambda self: float(
        self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.miscellaneous_income')))
    payment_date = fields.Datetime(string='Fecha de pago', default=fields.Datetime.now(), required=True, tracking=True)
    period_register = fields.Char(string='Periodo de registro', compute="compute_period_register", store=True)
    state = fields.Selection(
        [('draft', 'Borrador'), ('transfer', 'Transferencia bancaria'), ('ministry_defense', 'Ministerio de defensa')], default='draft', tracking=True)
    capital = fields.Float(string='Capital')
    interest = fields.Float(string='Interes')
    drawback = fields.Boolean(string='Reintegro')

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

    @api.depends('income', 'mandatory_contribution_certificate', 'miscellaneous_income', 'regulation_cup')
    def compute_voluntary_contribution_certificate(self):
        for record in self:
            record.voluntary_contribution_certificate = record.income - record.mandatory_contribution_certificate - record.miscellaneous_income - record.regulation_cup

    def confirm_payroll(self):
        for record in self:
            if record.state == 'draft':
                if record.income < 0:
                    raise ValidationError('El ingreso no puede ser menor o igual a cero')
                verify = record.partner_payroll_id.payroll_payments_ids.filtered(
                    lambda x: (x.state == 'transfer' or x.state == 'ministry_defense') and (
                                x.period_register == record.period_register))
                if len(verify) > 0 and record.drawback == False:
                    raise ValidationError('Ya existe un pago confirmado para este periodo')
                record.state = 'transfer'

    def return_draft(self):
        self.state = 'draft'

    def extract_numbers(self, text):
        numbers = re.findall(r'\d+', text)
        return [int(number) for number in numbers]

    @api.onchange('income', 'payment_date')
    def onchange_income(self):
        verify = len(self.partner_payroll_id.payroll_payments_ids.filtered(lambda x:x.miscellaneous_income == 10))
        if verify >= 1:
            self.miscellaneous_income = 0
        else:
            self.miscellaneous_income = self.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.miscellaneous_income')

        verify_certify = len(self.partner_payroll_id.payroll_payments_ids.search(
            [('mandatory_contribution_certificate', '>', '0'), ('state', '!=', 'draft')]))
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
                verify = record.partner_payroll_id.payroll_payments_ids.filtered(
                    lambda x: (x.state == 'ministry_defense' and x.period_register == record.period_register))
                if len(verify) > 0:
                    raise ValidationError('Ya existe un pago confirmado para este periodo')
                record.state = 'ministry_defense'
    # def write(self, vals):
    #     a = 1
    #     res = super(PayrollPayments, self).write(vals)
    #     return res

    @api.onchange('drawback')
    def onchange_drawback(self):
        for record in self:
            record.mandatory_contribution_certificate = 0
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
        view_id = self.env.ref('rod_cooperativa_aportes.payroll_payments_reports_tree_id').id
        return {
            'name': 'Detalle de aportes',
            'res_model': 'payroll.payments',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'tree',
            'domain': [],
        }


