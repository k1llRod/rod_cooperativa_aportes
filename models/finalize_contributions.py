from odoo import models, fields, api, _

class FinalizeContributions(models.Model):
    _name = 'finalize.contributions'
    _description = 'Finalize Contributions'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codigo', required=True)
    partner_payroll_id = fields.Many2one('partner.payroll', string='Codigo Aporte')
    date_finalize = fields.Date(string='Fecha de Finalizacion')
    disengagement = fields.Float(string='Desvinculacion', required=True, default=10)
    total_mandatory_contributions_certificate = fields.Float(string='Total de aportes obligatorios', required=True)
    total_voluntary_contributions_certificate = fields.Float(string='Total de aportes voluntarios', required=True)
    total_other_contributions = fields.Float(string='Total de otros aportes', required=True)
    total_surpluses = fields.Float(string='Total excedentes', required=True)
    total_performance_contributions = fields.Float(string='Total rendimiento de aportes', required=True)
    total_capital_initial = fields.Float('Total capital inicial')
    total_loan_capital = fields.Float(string='Total saldo de prestamo $')
    total_balance_total_interest_month = fields.Float(string='Total saldo interes mensual')
    default_dolar = fields.Float(string='Dolar $')
    total_loan_capital_bolivianos = fields.Float(string='Total saldo prestamo Bs.')
    total_balance_interest_month_bolivianos = fields.Float(string='Total saldo interes mensual Bs.')
    total_contributions = fields.Float(string='Total aportes', compute='_compute_total')
    total_loan = fields.Float(string='Total prestamo', compute='_compute_total_loan')
    partial_devolution = fields.Float(string="Devolucion parcial")
    regulation_cup_manual = fields.Float(string="Devolucion de tasa de regulacion")
    other_contribution_balance = fields.Float(string="Saldos extras")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Realizado'),
    ], string='Estado', default='draft')

    accounting_finalize_contributions_id = fields.Many2one('account.move', string='Asiento contable')
    accounting_finalize_contributions_state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
    ], string='Estado', default='draft', related='accounting_finalize_contributions_id.state', store=True,
        track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', string='Diario')
    account_contributions_id = fields.Many2one('account.account', string='Cuenta de aportes')
    account_voluntary_contribution_id = fields.Many2one('account.account', string='Cuenta de aporte Voluntario')
    account_mandatory_contribution_id = fields.Many2one('account.account', string='Cuenta de aporte obligatorio')
    account_other_contribution = fields.Many2one('account.account', string='Cuenta otras contribuciones')
    account_total_surplus = fields.Many2one('account.account', string='Cuenta excedentes de percepcion')

    account_capital_loan = fields.Many2one('account.account', string='Cuenta capital prestamo')
    account_month_surpluy = fields.Many2one('account.account', string='Cuenta dias excedentes')
    account_disengagement = fields.Many2one('account.account', string='Cuenta de desafiliacion')
    account_regulation_cup = fields.Many2one('account.account', string='Cuenta de tasa de regulacion')
    account_devolution_bank = fields.Many2one('account.account', string='Cuenta devolucion')
    account_other_contribution_balance = fields.Many2one('account.account', string='Cuenta otros aportes saldos')

    reafiliation = fields.Selection([
        ('passive_reserve_a','Pasivo categoria "A"'),
        ('passive_reserve_b','Pasivo categoria "B"')
        ], string='Reafiliacion como')
    partner_status_reafiliation = fields.Selection([('active', 'Activo'),
                                       ('active_reserve', 'Reserva activa'),
                                       ('passive', 'Servicio pasivo'),
                                       ], string="Situacion general",
                                        store=True)
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('finalize.contributions')
        return super(FinalizeContributions, self).create(vals)


    def finalize_contributions(self):
        # Here you can write the code to finalize the contributions
        return True

    def open_finalize_contributions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Liquidacion de aportes'),
            'res_model': 'finalize.contributions',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_draft(self):
        self.state = 'draft'

    def action_confirm(self):
        for record in self:
            if record.partner_payroll_id.state == 'process_finalized':
                record.partner_payroll_id.partner_status_especific_historical = record.partner_payroll_id.partner_status_especific
                record.partner_payroll_id.partner_status_historical = record.partner_payroll_id.partner_status
                create = self.env['partner.payroll'].create({
                    'partner_id': record.partner_payroll_id.partner_id.id,
                    # 'date': record.date_finalize,
                    # 'state': 'process',
                    'partner_status_especific_historical': record.reafiliation,
                    'partner_status_historical': record.partner_status_reafiliation,
                })
                if create:
                    record.partner_payroll_id.partner_id.partner_status_especific = record.reafiliation
                    record.state = 'done'
                    record.partner_payroll_id.state = 'finalized'
                    record.partner_payroll_id.state_finalize = 'hecho'
                    if record.partner_payroll_id.type_disengagement == 'fallecimiento':
                        record.partner_payroll_id.partner_id.state = 'deceased'
                    if record.partner_payroll_id.type_disengagement == 'retiro_voluntario':
                        record.partner_payroll_id.partner_id.state = 'unsubscribed'
            if record.partial_devolution > 0:
                a =1
                contribution_voluntary_total = record.total_capital_initial + record.total_voluntary_contributions_certificate
                val = []
                data = (0, 0, {'account_id': record.account_voluntary_contribution_id.id,
                               'debit': contribution_voluntary_total, 'credit': 0,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_mandatory_contribution_id.id,
                               'debit': record.total_mandatory_contributions_certificate, 'credit': 0,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_other_contribution.id,
                               'debit': record.total_other_contributions, 'credit': 0,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_total_surplus.id,
                               'debit': record.toal_perfomance_contributions, 'credit': 0,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_capital_loan.id,
                               'debit': 0, 'credit': record.total_loan_capital_bolivianos,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_month_surpluy.id,
                               'debit': 0, 'credit': record.total_balance_interest_month_bolivianos,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_disengagement.id,
                               'debit': 0, 'credit': record.disengagement,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_disengagement.id,
                               'debit': 0, 'credit': record.disengagement,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_devolution_bank.id,
                               'debit': 0, 'credit': record.partial_devolution,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_other_contribution_balance.id,
                               'debit': 0, 'credit': record.partial_devolution,
                               'partner_id': record.partner_id.id,
                               'amount_currency': 0
                               })
                val.append(data)
                


    @api.depends('total_mandatory_contributions_certificate', 'total_voluntary_contributions_certificate', 'total_other_contributions', 'total_surpluses', 'total_performance_contributions')
    def _compute_total(self):
        for record in self:
            record.total_contributions = record.total_capital_initial + record.total_mandatory_contributions_certificate + record.total_voluntary_contributions_certificate + record.total_other_contributions + record.total_surpluses + record.total_performance_contributions

    @api.depends('total_loan_capital', 'total_balance_total_interest_month')
    def _compute_total_loan(self):
        for record in self:
            record.total_loan = record.total_loan_capital_bolivianos + record.total_balance_interest_month_bolivianos


    def approve_finalize_contribution(self):
        val = []
        for record in self:
            total_contribution = record.total_capital_initial + record.total_mandatory_contributions_certificate
            data = (0, 0, {'account_id': record.account_voluntary_contribution_id.id,
                           'debit': total_contribution, 'credit': 0,
                           'partner_id': record.partner_id.id,
                           'amount_currency': 0
                           })
            val.append(data)
            if record.loan_historical_coaa > 0:
                amount = record.amount_loan - record.loan_historical_coaa
                # data = (0, 0, {'account_id': record.account_loan_id.id,
                #                          'debit': record.amount_loan, 'credit': 0, 'partner_id': record.partner_id.id,
                #                          'amount_currency': 0
                #                          })
                # val.append(data)
                data = (0, 0, {'account_id': record.account_loan_id.id,
                               'debit': 0, 'credit': record.loan_historical_coaa, 'partner_id': record.partner_id.id,
                               'name': 'COAA',
                               'amount_currency': 0
                               })
                val.append(data)
                data = (0, 0, {'account_id': record.account_loan_id.id,
                               'debit': 0, 'credit': amount, 'partner_id': record.partner_id.id,
                               'name': 'BENEFICIARIO',
                               'amount_currency': 0
                               })
                val.append(data)
            else:
                if record.refinance_loan_id:
                    amount_amortizacion = record.amount_loan - record.amount_devolution_bs - record.interest_day_rest_bs
                    amount_loan = record.amount_loan - (amount_amortizacion + record.interest_day_rest_bs)

                    data = (0, 0, {'account_id': record.account_egreso_id.id,
                                   'debit': 0, 'credit': amount_loan,
                                   # 'partner_id': record.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_monto_refinanciamiento.id,
                                   'debit': 0, 'credit': amount_amortizacion,
                                   # 'partner_id': record.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_monto_meses_interes.id,
                                   'debit': 0, 'credit': record.interest_day_rest_bs,
                                   # 'partner_id': record.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                else:
                    data = (0, 0, {'account_id': record.account_egreso_id.id,
                                   'debit': 0, 'credit': record.amount_loan,
                                   # 'partner_id': record.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
            if record.with_guarantor == 'loan_guarantor':
                glosa = "P/CONTAB. PREST. AMORT." + " " + record.partner_id.category_partner_id.code_loan + " " + record.partner_id.name + " COD: " + record.partner_id.code_contact + " PREST $US " + str(
                    record.amount_loan_dollars) + " INT " + str(
                    round(record.monthly_interest, 2)) + "% " + "F.CONTIGENCIA: " + str(
                    round(record.contingency_fund, 2)) + "% PLAZO: " + str(
                    record.months_quantity) + " MESES EXCED " + str(
                    record.surplus_days) + " DIAS " + "CUOTA FIJA $US: " + str(
                    round(record.loan_payment_ids[0].amount_total,
                          2)) + " GARANTES " + record.guarantor_one.category_partner_id.code_loan + " " + record.guarantor_one.name + " " + record.guarantor_two.category_partner_id.code_loan + " " + record.guarantor_two.name
            else:
                glosa = "P/CONTAB. PREST. AMORT." + " " + record.partner_id.category_partner_id.code_loan + " " + record.partner_id.name + " COD: " + record.partner_id.code_contact + " PREST $US " + str(
                    record.amount_loan_dollars) + " INT " + str(
                    round(record.monthly_interest, 2)) + "% " + "F.CONTIGENCIA: " + str(
                    round(record.contingency_fund, 2)) + "% PLAZO: " + str(
                    record.months_quantity) + " MESES EXCED " + str(
                    record.surplus_days) + " DIAS " + "CUOTA FIJA $US: " + str(
                    round(record.loan_payment_ids[0].amount_total, 2))
            move_vals = {
                "date": record.date_approval,
                "journal_id": record.journal_id.id,
                "ref": "PRESTAMOS ASIGNADO AL ASOCIADO" + " " + record.partner_id.name + " EN LA FECHA " + str(
                    record.date_approval),
                # "company_id": payment.company_id.id,
                # "name": "name test",
                "glosa": glosa,
                "state": "draft",
                "line_ids": val,
            }
            account_move_id = record.env['account.move'].create(move_vals)
            record.accounting_entry_id = account_move_id.id
            account_move_id.loan_application_id = record.id
        return {
            'name': 'Pagos de planilla',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': account_move_id.id,
            'views': [(False, 'form')],
        }
