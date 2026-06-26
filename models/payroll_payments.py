from encodings.punycode import digits
from xml import etree

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re
from dateutil.relativedelta import relativedelta


class PayrollPayments(models.Model):
    _name = 'payroll.payments'
    _description = 'Pagos individuales de planilla'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='ID aporte')
    partner_payroll_id = fields.Many2one('partner.payroll', string='Planilla de socio')
    partner_name = fields.Char(String='Nombre del socio', related='partner_payroll_id.partner_id.name', store=True)
    partner_code_contact = fields.Char(string='Codigo de socio', related='partner_payroll_id.partner_id.code_contact',
                                       store=True)
    partner_status = fields.Selection([('active', 'Activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive', 'Servicio pasivo'),
                                       ('leave', 'Baja'),], string="Situacion general",
                                      related='partner_payroll_id.partner_id.partner_status', store=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado',
                                                related='partner_payroll_id.partner_id.partner_status_especific',
                                                store=True)
    city = fields.Char(string='Ciudad', related='partner_payroll_id.partner_id.city', store=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        default=lambda self: self.env.company, index=True
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        related='company_id.currency_id', store=True, readonly=True
    )
    income = fields.Monetary(string='DESC. MINDEF',currency_field='currency_id', required=True, tracking=True)
    income_passive = fields.Monetary(string='DESC. PASIVO', required=True, tracking=True, currency_field='currency_id')
    mandatory_contribution_certificate = fields.Monetary(string='CERT. APOR. OBLI.', default=0.0,
                                                         currency_field='currency_id')
    voluntary_contribution_certificate = fields.Monetary(
        string='CERT. APOR. VOL.', compute="compute_voluntary_contribution_certificate", store=True,
        currency_field='currency_id'
    )
    regulation_cup = fields.Monetary(
        string='TASA REGULACION',
        default=lambda self: float(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.regulation_cup')),
        currency_field='currency_id'
    )
    payment_post_mortem = fields.Monetary(string='PAGO POST MORTEM', currency_field='currency_id')
    miscellaneous_income = fields.Monetary(string='INSCRIPCION', currency_field='currency_id')
    payment_date = fields.Date(string='Fecha de pago', default=fields.Datetime.now(), required=True, tracking=True)
    period_register = fields.Char(string='Periodo de registro', compute="compute_period_register", store=True)
    state = fields.Selection(
        [('draft', 'Borrador'),
         ('transfer', 'Transferencia bancaria'),
         ('ministry_defense', 'Ministerio de defensa'),
         ('contribution_interest', 'Aporte y rendimiento COAA'),
         ('no_contribution', 'Sin aporte'),
         ('capital_initial','Capital inicial'),
         ('partner_return', 'Devolucion'),
         ('partner_return_credit','Dev. Credito'),
         ('other_contribution','Otros aportes Cooperativa'),
         ('other_contribution_coaa','Otros aportes COAA'),
         ('disengagement','Desvinculacion'),
         ('surpluses','Excedentes')],
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
    date_pivote = fields.Date(string='Fecha de pivote', default=fields.Datetime.now() - relativedelta(months=1),
                                  tracking=True)
    number_correlative = fields.Char(string='Numero correlativo')
    date_register_correlative = fields.Date(string='Fecha de registro')
    calculate_mandatory_contribution_total = fields.Float(string='Total aporte obligatorio certificado')

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
    journal_id = fields.Many2one('account.journal', string='Diario')

    account_move_id = fields.Many2one('account.move', string='Asiento contable')

    capital_initial = fields.Float(string='Capital inicial')
    state_account = fields.Selection([('draft', 'Borrador'), ('posted', 'Contabilizado'), ('cancel', 'Cancelado')], default='draft', related='account_move_id.state', store=True)
    other = fields.Monetary(string='Otros', currency_field='currency_id')
    other_contribution = fields.Monetary(string='OTROS APORTES', currency_field='currency_id', digits=(12, 2))
    # @api.onchange('payment_date')
    # def onchange_payment_date(self):
    #     for record in self:
    #         if self.payment_date:
    #             record.period_register = record.payment_date.strftime('%m') + '/' + record.payment_date.strftime('%Y')
    # @api.onchange('date_pivote')
    # def onchange_date_pivote(self):
    #     for record in self:
    #         if self.date_pivote:
    #             record.period_register = record.date_pivote.strftime('%m') + '/' + record.date_pivote.strftime('%Y')

    @api.depends('date_pivote')
    def compute_period_register(self):
        for record in self:
            record.period_register = record.date_pivote.strftime('%m') + '/' + record.date_pivote.strftime('%Y')

    @api.model
    def create(self, vals_list):
        name = self.env['ir.sequence'].next_by_code('payroll.payments')
        vals_list['name'] = name
        res = super(PayrollPayments, self).create(vals_list)
        res.account_income_id = res.partner_payroll_id.account_income_id
        res.account_inscription_id = res.partner_payroll_id.account_inscription_id
        res.account_regulation_cup_id = res.partner_payroll_id.account_regulation_cup_id
        res.account_mandatory_contribution_id = res.partner_payroll_id.account_mandatory_contribution_id
        res.account_voluntary_contribution_id = res.partner_payroll_id.account_voluntary_contribution_id
        # if len(res.partner_payroll_id.payroll_payments_ids) == 1:
        #     res.partner_payroll_id.date_burn_partner = fields.Datetime.now()
        #     if res.partner_payroll_id.partner_status_especific == 'active_service' or res.partner_payroll_id.partner_status_especific == 'letter_a' or res.partner_payroll_id.partner_status_especific == 'passive_reserve_b':
        #         res.partner_payroll_id.state = 'process'
        if vals_list['income'] > 0:
            res.partner_payroll_id.message_post(body="Pago creado: " + vals_list['name'])
        # else:
        #     res.partner_payroll_id.message_post(body="Devolucion creada: " + vals_list['name'])

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

    @api.depends('income', 'mandatory_contribution_certificate', 'miscellaneous_income',
                 'regulation_cup', 'historical_contribution_coaa', 'historical_interest_coaa','capital_initial')
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
                if record.capital_initial > 0:
                    record.voluntary_contribution_certificate = record.capital_initial
                    record.regulation_cup = 0
                    record.miscellaneous_income = 0
                    record.mandatory_contribution_certificate = 0
                    record.income_passive = 0
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
                if len(verify) > 0 and record.drawback == False and record.partner_status != 'passive':
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
        self.partner_payroll_id.compute_count_pay_contributions()

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
        if verify_certify == 0 and self.partner_payroll_id.partner_status_especific != 'passive_reserve_b':
            self.mandatory_contribution_certificate = 100
            return

        month_flag = self.extract_numbers(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.month_ids'))
        sw = 0
        if self.partner_payroll_id.partner_status_especific != 'passive_reserve_b':
            for month in month_flag:
                if month == self.date_pivote.month and self.drawback == False:
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
            # 'view_id': view_id,
            'view_mode': 'tree,form,pivot',
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
            record.partner_payroll_id.compute_count_pay_contributions()

    def draft_massive(self):
        for record in self:
            record.state = 'draft'

    def create_account_move(self,income=False,income_passive=False,inscription=False,regulation_cup=False,mandatory_contribution=False,voluntary_contribution=False):
        for rec in self:
            move_line_vals = []
            move_line = []
            journal_id = rec.journal_id.id
            if not income:
                income = rec.account_income_id
            if not income_passive:
                income_passive = rec.account_income_id
                # income_passive = rec.account_income_id if rec.income == False else rec.partner_payroll_id.income
            if not inscription:
                inscription = rec.account_inscription_id
            if not regulation_cup:
                regulation_cup = rec.account_regulation_cup_id
            if not mandatory_contribution:
                mandatory_contribution = rec.account_mandatory_contribution_id
            if not voluntary_contribution:
                voluntary_contribution = rec.account_voluntary_contribution_id
            if rec.state == 'ministry_defense' or rec.state == 'transfer':
                data = (0, 0, {'account_id': income.id if income.id != False else rec.partner_payroll_id.account_income_id.id,
                                         'debit': rec.income_passive if rec.income == 0 else rec.income, 'credit': 0, 'partner_id': rec.partner_payroll_id.partner_id.id,
                                         'amount_currency': 0
                                         })
                if not (rec.income_passive == 0 and rec.income == 0): move_line.append(data)
                data = (0, 0, {'account_id': inscription.id if inscription.id != False else rec.partner_payroll_id.account_inscription_id.id,
                                          'debit': 0, 'credit': rec.miscellaneous_income, 'partner_id': rec.partner_payroll_id.partner_id.id,
                                         'amount_currency': 0
                                         })
                if not (rec.miscellaneous_income == 0): move_line.append(data)
                data = (0, 0, {'account_id': regulation_cup.id if regulation_cup.id != False else rec.partner_payroll_id.account_regulation_cup_id.id,
                                         'debit': 0, 'credit': rec.regulation_cup, 'partner_id': rec.partner_payroll_id.partner_id.id,
                                         'amount_currency': 0
                                         })

                if not (rec.regulation_cup == 0): move_line.append(data)
                data = (0, 0, {'account_id': mandatory_contribution.id if mandatory_contribution.id != False else rec.partner_payroll_id.account_mandatory_contribution_id.id,
                                         'debit': 0, 'credit': rec.mandatory_contribution_certificate, 'partner_id': rec.partner_payroll_id.partner_id.id,
                                         'amount_currency': 0
                                         })
                if not (rec.mandatory_contribution_certificate == 0): move_line.append(data)
                data = (0, 0, {'account_id': voluntary_contribution.id if voluntary_contribution.id != False else rec.partner_payroll_id.account_voluntary_contribution_id.id,
                                         'debit': 0, 'credit': rec.voluntary_contribution_certificate, 'partner_id': rec.partner_payroll_id.partner_id.id,
                                         'amount_currency': 0
                                         })
                if not(rec.voluntary_contribution_certificate == 0): move_line.append(data)
            if rec.state == 'contribution_interest' or rec.state == 'capital_initial':
                total = rec.historical_contribution_coaa + rec.historical_interest_coaa
                data = (0, 0, {'account_id': income.id,
                                         'debit': rec.income_passive if rec.income_passive > 0 else total, 'credit': 0, 'partner_id': rec.partner_payroll_id.partner_id.id,
                                         'amount_currency': 0
                                         })
                move_line.append(data)
                data = (0, 0, {
                    'account_id': inscription.id if inscription.id != False else rec.partner_payroll_id.account_inscription_id.id,
                    'debit': 0, 'credit': rec.miscellaneous_income, 'partner_id': rec.partner_payroll_id.partner_id.id,
                    'amount_currency': 0
                    })
                if not (rec.miscellaneous_income == 0): move_line.append(data)
                data = (0, 0, {
                    'account_id': regulation_cup.id if regulation_cup.id != False else rec.partner_payroll_id.account_regulation_cup_id.id,
                    'debit': 0, 'credit': rec.regulation_cup, 'partner_id': rec.partner_payroll_id.partner_id.id,
                    'amount_currency': 0
                    })

                if not (rec.regulation_cup == 0): move_line.append(data)
                data = (0, 0, {
                    'account_id': mandatory_contribution.id if mandatory_contribution.id != False else rec.partner_payroll_id.account_mandatory_contribution_id.id,
                    'debit': 0, 'credit': rec.mandatory_contribution_certificate,
                    'partner_id': rec.partner_payroll_id.partner_id.id,
                    'amount_currency': 0
                    })
                if not (rec.mandatory_contribution_certificate == 0): move_line.append(data)
                data = (0, 0, {
                    'account_id': voluntary_contribution.id if voluntary_contribution.id != False else rec.partner_payroll_id.account_voluntary_contribution_id.id,
                    'debit': 0, 'credit': rec.voluntary_contribution_certificate,
                    'partner_id': rec.partner_payroll_id.partner_id.id,
                    'amount_currency': 0
                    })
                if not (rec.voluntary_contribution_certificate == 0): move_line.append(data)
            move_vals = {
                "date": rec.payment_date,
                "journal_id": journal_id if journal_id != False else rec.partner_payroll_id.journal_id.id,
                "ref": "Aporte de socio" + " " +rec.partner_payroll_id.partner_id.name + " " + rec.period_register,
                # "company_id": payment.company_id.id,
                # "name": "name test",
                "state": "draft",
                "line_ids": move_line,
            }
            account_move_id = rec.env['account.move'].create(move_vals)
            rec.account_move_id = account_move_id.id
            account_move_id.payroll_payment_id = rec.id
    def no_contribution(self):
        for record in self:
            verify = record.partner_payroll_id.payroll_payments_ids.filtered(
                lambda x: (x.state == 'ministry_defense' and x.period_register == record.period_register))
            if len(verify) > 0:
                raise ValidationError('Ya existe un pago confirmado para este periodo')
            record.miscellaneous_income = 0
            record.regulation_cup = 0
            record.mandatory_contribution_certificate = 0
            record.voluntary_contribution_certificate = 0
            record.state = 'no_contribution'
            record.partner_payroll_id.compute_count_pay_contributions()


    def capital_initial_a(self):
        for record in self:
            record.state = 'capital_initial'
            record.partner_payroll_id.compute_count_pay_contributions()

    def other_contributions(self):
        for record in self:
            record.state = 'other_contribution'
            record.partner_payroll_id.compute_count_pay_contributions()

    def surpluses(self):
        for record in self:
            record.state = 'surpluses'
            record.partner_payroll_id.compute_count_pay_contributions()

    def disengagement(self):
        for record in self:
            record.state = 'disengagement'

    def agroup_payroll_payments(self):
        payment_date = self[0].payment_date
        period = self[0].period_register
        sw = 0
        val = []
        for record in self:
            if record.state == 'draft':
                raise ValidationError('No se pueden validar pagos en estado "BORRADOR"')
            val.append(record.income if record.income != 0 else record.income_passive)
            if record.payment_date != payment_date:
                sw = 1
        if sw == 1:
            raise ValidationError('No se pueden validar pagos con fechas diferentes')
        other_contribution = len(self.filtered(lambda x:x.state == 'other_contribution' or x.state == 'surpluses'))
        if other_contribution > 0:
            total_income = round(sum(self.mapped('other_contribution')),2)
        else:
            total_income = round(sum(self.mapped('income')),2) if sum(self.mapped('income')) > 0 else round(sum(self.mapped('income_passive')),2)
        if sum(self.mapped('income')) < 0:
            total_income = round(sum(self.mapped('income')),2)
        if round(sum(self.mapped('historical_contribution_coaa')),2) > 0 and sum(self.mapped('historical_interest_coaa')) > 0:
            total_income = round(sum(self.mapped('voluntary_contribution_certificate')),2)
        total_miscellaneous_income = sum(self.mapped('miscellaneous_income'))
        total_regulation_cup = sum(self.mapped('regulation_cup'))
        total_mandatory_contribution = sum(self.mapped('mandatory_contribution_certificate'))
        total_voluntary_contribution = sum(self.mapped('voluntary_contribution_certificate')) if other_contribution == 0 else sum(self.mapped('other_contribution'))
        amount_total = total_miscellaneous_income + total_regulation_cup + total_mandatory_contribution + total_voluntary_contribution
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.payroll.payments',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_total_income': total_income,
                'default_payment_date': payment_date,
                'default_total_miscellaneous_income': total_miscellaneous_income,
                'default_total_regulation_cup': total_regulation_cup,
                'default_total_mandatory_contribution': total_mandatory_contribution,
                'default_total_voluntary_contribution': total_voluntary_contribution,
                'default_amount_total': amount_total,
                'default_val': self.ids,
                'default_period':period,
            }
        }

    @api.onchange('date_register_correlative')
    def onchange_date_register_correlative(self):
        for rec in self:
            if rec.mandatory_contribution_certificate < 100:
                raise ValidationError('El aporte obligatorio debe ser mayor a 100')
            if rec.date_register_correlative:
                register = rec.partner_payroll_id.payroll_payments_ids.filtered(lambda x:x.mandatory_contribution_certificate == 100 and x.date_pivote <= rec.date_pivote)
                rec.calculate_mandatory_contribution_total = sum(register.mapped('mandatory_contribution_certificate'))

    def partner_devolution(self):
        for record in self:
            record.state = 'partner_return'
            record.partner_payroll_id.compute_count_pay_contributions()

    def partner_devolution_credit(self):
        for record in self:
            record.state = 'partner_return_credit'
            record.partner_payroll_id.compute_count_pay_contributions()
