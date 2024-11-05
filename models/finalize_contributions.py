from odoo import models, fields, api, _

class FinalizeContributions(models.Model):
    _name = 'finalize.contributions'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codigo')
    date_proccess = fields.Date(string='Fecha de proceso')
    partner_payroll_ids = fields.Many2one('partner.payroll', string='Aportes')
    loan_application_ids = fields.Many2one('loan.application', string='Prestamo')
    disengagement = fields.Float('Desvinculacion')
    total_mandatory_contributions = fields.Float(string='Total de aportes obligatorios', digits=(16,2))
    total_voluntary_contributions = fields.Float(string='Total de aportes voluntarios', digits=(16,2))
    total_capital_initial = fields.Float('Total capital inicial', digits=(16,2))
    total_voluntary = fields.Float('Total aportes', compute='calculate_total_voluntary', digits=(16,2))
    total_diference_contribution_loan = fields.Float(string='Diferencia aportes - prestamo', compute='calculate_diference_contribution_loan', digits=(16,2))
    state = fields.Selection([('draft', 'Borrador'),
                                      ('done', 'Confirmado')],
                                     string='Estado', default='draft')

    loan_capital_bolivianos = fields.Float(string='Total capital prestamo', digits=(16,2))
    balance_interest_month_bolivianos = fields.Float(string='Total dias de interes', digits=(16,2))
    discount_contribution = fields.Float(string='Descuento aporte', digits=(16,2))

    journal_id = fields.Many2one('account.journal', string='Diario')
    account_move_id = fields.Many2one('account.move', string='Asiento contable')
    account_voluntary_contributions = fields.Many2one('account.account', string='Aportes voluntarios')

    account_capital_loan = fields.Many2one('account.account', string='Capital credito')
    account_interest_month = fields.Many2one('account.account', string='Interes mensual')
    account_bank_rest = fields.Many2one('account.account', string='Banco saldo restante')

    @api.depends('total_voluntary_contributions','total_capital_initial')
    def calculate_total_voluntary(self):
        for record in self:
            total = record.total_voluntary_contributions + record.total_capital_initial
            record.total_voluntary = total


    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('finalize.contributions')
        vals['name'] = name
        res = super(FinalizeContributions, self).create(vals)
        return res

    def open_finalize_contributions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Liquidacion de aportes'),
            'res_model': 'finalize.contributions',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    @api.depends('discount_contribution','loan_capital_bolivianos','balance_interest_month_bolivianos')
    def calculate_diference_contribution_loan(self):
        for record in self:
            total_loan = record.loan_capital_bolivianos + record.balance_interest_month_bolivianos
            record.total_diference_contribution_loan = record.discount_contribution - total_loan

    def action_confirm(self):
        for record in self:
            if record.partner_payroll_ids.state == 'process':
                vals = {}
                if record.total_diference_contribution_loan == 0:
                    vals = {
                        'partner_payroll_id': record.partner_payroll_ids.id,
                        'income': 0,
                        'income_passive': 0,
                        'miscellaneous_income': 0,
                        'regulation_cup': 0,
                        'mandatory_contribution_certificate': 0,
                        'voluntary_contribution_certificate': record.discount_contribution,
                        'other_contribution': 0,
                        'payment_date': record.date_proccess,
                        'date_pivote': record.date_proccess,
                    }
                    payroll = self.env['payroll.payments'].create(vals)
                    payroll.write({
                        'voluntary_contribution_certificate': -(record.discount_contribution),
                    })
                    payroll.partner_devolution()
                    if payroll:
                        val=[]
                        data = (0, 0, {'account_id': record.account_voluntary_contributions.id,
                                       'debit': record.discount_contribution, 'credit': 0,
                                       'partner_id': record.partner_payroll_ids.partner_id.id,
                                       'amount_currency': 0
                                       })
                        val.append(data)
                        data = (0, 0, {'account_id': record.account_capital_loan.id,
                                       'debit': 0, 'credit': record.loan_capital_bolivianos,
                                       'partner_id': record.partner_payroll_ids.partner_id.id,
                                       'amount_currency': 0
                                       })
                        val.append(data)
                        data = (0, 0, {'account_id': record.account_interest_month.id,
                                       'debit': 0, 'credit': record.balance_interest_month_bolivianos,
                                       'partner_id': record.partner_payroll_ids.partner_id.id,
                                       'amount_currency': 0
                                       })
                        val.append(data)
                        move_vals = {
                            "date": record.date_proccess,
                            "journal_id": record.journal_id.id,
                            "ref": "",
                            # "company_id": payment.company_id.id,
                            # "name": "name test",
                            "glosa": '',
                            "state": "draft",
                            "line_ids": val,
                        }
                        account_move_id = record.env['account.move'].create(move_vals)
                        record.account_move_id = account_move_id.id
                        account_move_id.finalize_contributions_id = record.id
                        finalized_loan = self.env['finalized.loan'].create({
                            'loan_application_id': self.loan_application_ids.id,
                            'date_finalize': self.date_proccess,
                            'amount_loan_dollars_initial': record.loan_application_ids.amount_loan_dollars,
                            'amount_loan_initial': record.loan_application_ids.amount_loan,
                            'payment_count': record.loan_application_ids.total_payments_confirm,
                            'balance_capital_dollar': record.loan_application_ids.balance_capital,
                            'balance_capital_bolivianos': record.loan_capital_bolivianos,
                            'balance_total_interest_month': record.loan_application_ids.balance_total_interest_month,
                            'balance_total_interest_month_bolivianos': record.balance_interest_month_bolivianos,
                            'state': 'draft'
                        })
                        if finalized_loan:
                            record.loan_application_ids.state = 'liquidation_process'
                            finalized_loan.action_confirm()
                        return {
                            'name': 'Pagos de planilla',
                            'type': 'ir.actions.act_window',
                            'res_model': 'account.move',
                            'view_mode': 'form',
                            'res_id': account_move_id.id,
                            'views': [(False, 'form')],
                        }
                        # record.accounting_entry_id = account_move_id.id
                        # account_move_id.loan_application_id = record.id