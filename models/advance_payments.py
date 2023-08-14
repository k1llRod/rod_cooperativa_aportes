from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re



class AdvancePayments(models.Model):
    _name = 'advance.payments'
    _description = 'Advance Payments'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Date(string='Fecha')
    n_months = fields.Integer(string='N° Meses')
    regulation_cup = fields.Float(string='Tasa de regulación')
    mandatory_contribution = fields.Float(string='Aporte obligatorio')
    contribution_passive = fields.Float(string='Aporte pasivo')
    advanced_partner_payroll_id = fields.Many2one('partner.payroll', string='Pagos adelantados')
    remaining_regulation_cup = fields.Float(string='Tasa de regulación restante', compute='compute_partner_payroll', store=True)
    remaining_mandatory_contribution = fields.Float(string='Aporte obligatorio restante', compute='compute_partner_payroll', store=True)
    remaining_contribution_passive = fields.Float(string='Aporte pasivo restante', compute='compute_partner_payroll', store=True)
    miscellaneous_income = fields.Float(string='Inscripcion', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.miscellaneous_income'))
    state = fields.Selection([('draft', 'Borrador'), ('process','En proceso'),('done', 'Finalizado')], string='Estado', default='draft')

    # def compute_partner_payroll(self):
    #     for record in self:
    #         record.remaining_regulation_cup = 1
    #         record.remaining_mandatory_contribution = 1
    #         record.remaining_contribution_passive = 1
    @api.depends('advanced_partner_payroll_id.count_pay_contributions')
    def compute_partner_payroll(self):
        for record in self:
            record.remaining_regulation_cup = record.regulation_cup - sum(record.advanced_partner_payroll_id.payroll_payments_ids.filtered(lambda x:x.advanced_automata == True and (x.state == 'transfer' or x.state == 'ministry_defense')).mapped('regulation_cup'))
            record.remaining_mandatory_contribution = record.mandatory_contribution - sum(record.advanced_partner_payroll_id.payroll_payments_ids.filtered(lambda x:x.advanced_automata == True and (x.state == 'transfer' or x.state == 'ministry_defense')).mapped('mandatory_contribution_certificate'))
            record.remaining_contribution_passive = record.contribution_passive - (sum(record.advanced_partner_payroll_id.payroll_payments_ids.filtered(lambda x:x.advanced_automata == True and (x.state == 'transfer' or x.state == 'ministry_defense')).mapped('voluntary_contribution_certificate')))
                                                                                   # sum(record.advanced_partner_payroll_id.payroll_payments_ids.filtered(lambda x:x.advanced_automata == True and (x.state == 'transfer' or x.state == 'ministry_defense')).mapped('regulation_cup')))

    @api.onchange('n_months')
    def onchange_n_months(self):
        if self.n_months:
            # self.name = datetime.now()
            self.regulation_cup = float(self.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.regulation_cup')) * self.n_months
            periods = self.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.month_ids')
            filter_periods = list(map(int, re.findall(r'\d+', periods)))
            count_periods = len(filter_periods)
            count = 12 / count_periods
            self.mandatory_contribution = float(self.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.mandatory_contribution_certificate')) * count_periods

            self.contribution_passive = float(self.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.contribution_passive')) * self.n_months

    def create_lines_payments(self):
        for record in self:
            year = datetime.now().year
            month = 1
            # res_currency = round(record.env['res.currency'].search([('name', '=', 'USD')], limit=1).inverse_rate,2)
            chain_data = []
            first_day_month = datetime(year, month, 1,8,00,00)
            income_passive = float(record.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.contribution_passive'))
            periods = record.env['ir.config_parameter'].sudo().get_param(
                'rod_cooperativa_aportes.month_ids')
            filter_periods = list(map(int, re.findall(r'\d+', periods)))
            count_periods = len(filter_periods)
            count = 12 / count_periods
            n_reg_records = int(record.regulation_cup / float(
                record.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.regulation_cup')))
            n_mand_records = int(count * (record.mandatory_contribution / float(
                record.env['ir.config_parameter'].sudo().get_param(
                    'rod_cooperativa_aportes.mandatory_contribution_certificate'))))
            if n_mand_records == n_reg_records:
                record.state = 'process'
                for n_reg_records in range(1, n_reg_records + 1):
                    income_passive_data = income_passive + float(record.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.regulation_cup'))
                    if n_reg_records == 1:
                        miscellaneous_income = float(record.env['ir.config_parameter'].sudo().get_param(
                            'rod_cooperativa_aportes.miscellaneous_income'))
                        income_passive_data = miscellaneous_income + income_passive_data
                    else:
                        miscellaneous_income = 0

                    if n_reg_records in filter_periods:
                        mandatory_contribution = float(record.env['ir.config_parameter'].sudo().get_param(
                            'rod_cooperativa_aportes.mandatory_contribution_certificate'))
                        income_passive_data = mandatory_contribution + income_passive_data
                    else:
                        mandatory_contribution = 0
                    first_day_month = datetime(year, month, 1,8,00,00)
                    record.advanced_partner_payroll_id.payroll_payments_ids.create({
                        'income': 0,
                        'income_passive': income_passive_data,
                        'regulation_cup': record.env['ir.config_parameter'].sudo().get_param(
                            'rod_cooperativa_aportes.regulation_cup'),
                        'payment_date': first_day_month,
                        'miscellaneous_income': miscellaneous_income,
                        'mandatory_contribution_certificate': mandatory_contribution,
                        'advanced_automata':True,
                        'partner_payroll_id': record.advanced_partner_payroll_id.id,
                        'register_advanced_payments_ids':record.id,
                    })

                    month += 1
    def draft_lines_payments(self):
        self.state = 'draft'

    def action_pdf_payment_note(self):
        return self.env.ref('rod_cooperativa_aportes.action_report_pdf_payment_note').report_action(self)