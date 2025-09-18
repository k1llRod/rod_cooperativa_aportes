from odoo import models, fields, api, _
from num2words import num2words


class FinalizeContributions(models.Model):
    _name = 'finalize.contributions'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codigo')
    liquidation = fields.Boolean(string='Liquidar prestamo', default=False)
    liquidation_contributions = fields.Boolean(string="Liquidar aportes", default=False)
    date_proccess = fields.Date(string='Fecha de proceso')
    partner_payroll_ids = fields.Many2one('partner.payroll', string='Aportes')
    loan_application_ids = fields.Many2one('loan.application', string='Prestamo')
    disengagement = fields.Float('Desvinculacion')
    regulation_cup = fields.Float('Tasa de regulacion')
    total_mandatory_contributions = fields.Float(string='Total de aportes obligatorios', digits=(16, 2))
    total_voluntary_contributions = fields.Float(string='Total de aportes voluntarios', digits=(16, 2))
    total_capital_initial = fields.Float('Total capital inicial', digits=(16, 2))
    total_voluntary = fields.Float('Total aportes voluntarios', compute='calculate_total_voluntary', digits=(16, 2))
    total_amount = fields.Float(string='Total Debe', compute='calculate_total_amount', digits=(16, 2))
    total_amount_credit = fields.Float(string='Total Haber', compute='calculate_amount_credit', digits=(16, 2))
    manual_regulation_cup = fields.Float(string="Tasa de regulacion manual", digits=(16, 2))
    manual_post_mortem = fields.Float(string="Post mortem manual", digits=(16, 2))
    manual_aporte_obligatorio = fields.Float(string="Aporte obligatorio manual", digits=(16, 2))
    rest_contributions = fields.Float(string="Monto restante aportes", compute='calculate_rest_contributions',
                                      digits=(16, 2))
    other_contributions = fields.Float('Total otros aportes', digits=(16, 2))
    surpluses = fields.Float('Total excedentes', digits=(16, 2))
    perfomance_contributions = fields.Float('Total rendimiento', digits=(16, 2))

    total_diference_contribution_loan = fields.Float(string='Diferencia aportes - prestamo',
                                                     compute='calculate_diference_contribution_loan', digits=(16, 2))
    total_partial_devolution = fields.Float(string="Devolucion parcial")
    state = fields.Selection([('draft', 'Borrador'),
                              ('done', 'Confirmado')],
                             string='Estado', default='draft')

    loan_capital_bolivianos = fields.Float(string='Total capital prestamo', digits=(16, 2))
    balance_interest_month_bolivianos = fields.Float(string='Total dias de interes', digits=(16, 2))
    discount_contribution = fields.Float(string='Descuento aporte', digits=(16, 2))


    journal_id = fields.Many2one('account.journal', string='Diario')
    account_move_id = fields.Many2one('account.move', string='Asiento contable')
    account_voluntary_contributions = fields.Many2one('account.account', string='Cuenta Aportes voluntarios')
    account_mandatory_contributions = fields.Many2one('account.account', string='Cuenta Aportes Obligatorios')
    account_other_contributions = fields.Many2one('account.account', string='Cuenta Otros aportes')
    account_surpluses = fields.Many2one('account.account', string='Cuenta Excedentes')
    account_performance_contributions = fields.Many2one('account.account', string='Rendimiento')

    account_capital_loan = fields.Many2one('account.account', string='Cuenta Capital credito')
    account_interest_month = fields.Many2one('account.account', string='Cuenta Interes mensual')
    account_bank_rest = fields.Many2one('account.account', string='Cuenta Banco saldo restante')

    account_disengagement = fields.Many2one('account.account', string='Cuenta de desvinculacion')
    account_regulation_cup = fields.Many2one('account.account', string='Cuenta tasa de regulacion')
    account_bank_rest_contributions = fields.Many2one('account.account', string='Cuenta Banco aportes restantes')
    account_manual_post_mortem = fields.Many2one('account.account', string='Cuenta Post mortem manual')
    account_manual_aporte_obligatorio = fields.Many2one('account.account', string='Cuenta Aporte obligatorio manual')

    literal_number = fields.Char(string='Amount literal', compute='_compute_literal_number')

    @api.depends('total_voluntary_contributions', 'total_capital_initial')
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

    @api.depends('discount_contribution', 'loan_capital_bolivianos', 'balance_interest_month_bolivianos')
    def calculate_diference_contribution_loan(self):
        for record in self:
            if record.liquidation == True and record.liquidation_contributions == True:
                total_loan = record.loan_capital_bolivianos + record.balance_interest_month_bolivianos
                record.total_diference_contribution_loan = record.total_amount - total_loan
            else:
                total_loan = record.loan_capital_bolivianos + record.balance_interest_month_bolivianos
                record.total_diference_contribution_loan = record.discount_contribution - total_loan

    @api.depends('total_voluntary_contributions', 'total_capital_initial', 'other_contributions', 'surpluses',
                 'perfomance_contributions', 'total_mandatory_contributions')
    def calculate_total_amount(self):
        for record in self:
            total = record.total_voluntary_contributions + record.total_capital_initial + record.other_contributions + record.surpluses + record.perfomance_contributions + record.total_mandatory_contributions
            record.total_amount = total

    @api.depends('disengagement', 'manual_regulation_cup', 'rest_contributions')
    def calculate_amount_credit(self):
        for record in self:
            record.total_amount_credit = record.disengagement + record.manual_regulation_cup + record.rest_contributions + record.loan_capital_bolivianos + record.balance_interest_month_bolivianos + record.manual_post_mortem + record.manual_aporte_obligatorio

    @api.depends('manual_regulation_cup', 'disengagement','manual_post_mortem', 'manual_aporte_obligatorio')
    def calculate_rest_contributions(self):
        for record in self:
            if record.total_partial_devolution > 0:
                record.rest_contributions = record.total_partial_devolution
            else:
                record.rest_contributions = record.total_amount - record.disengagement - record.manual_regulation_cup - record.loan_capital_bolivianos - record.balance_interest_month_bolivianos - record.manual_post_mortem - record.manual_aporte_obligatorio

    def action_confirm(self):
        for record in self:
            if record.partner_payroll_ids.state == 'process':
                vals = {}
                if record.total_diference_contribution_loan == 0 and record.liquidation == True:
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
                        val = []
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
                            "partner_id": record.partner_payroll_ids.partner_id.id,
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
                            finalized_loan.accounting_finalized_loan_id = account_move_id.id
                            record.loan_application_ids.loan_payment_ids.filtered(lambda x:x.name == 'LIQUID 1').account_move_id = account_move_id.id
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

                if record.liquidation_contributions == True and record.liquidation == False:
                    val = []
                    data = (0, 0, {'account_id': record.account_voluntary_contributions.id,
                                   'debit': record.total_voluntary, 'credit': 0,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_mandatory_contributions.id,
                                   'debit': record.total_mandatory_contributions, 'credit': 0,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_other_contributions.id,
                                   'debit': record.other_contributions, 'credit': 0,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_surpluses.id,
                                   'debit': record.surpluses, 'credit': 0,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_disengagement.id,
                                   'debit': 0, 'credit': record.disengagement,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_regulation_cup.id,
                                   'debit': 0, 'credit': record.manual_regulation_cup,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_bank_rest_contributions.id,
                                   'debit': 0, 'credit': record.rest_contributions,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_manual_aporte_obligatorio.id,
                                   'debit': 0, 'credit': record.manual_aporte_obligatorio,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    data = (0, 0, {'account_id': record.account_manual_post_mortem.id,
                                   'debit': 0, 'credit': record.manual_post_mortem,
                                   'partner_id': record.partner_payroll_ids.partner_id.id,
                                   'amount_currency': 0
                                   })
                    val.append(data)
                    move_vals = {
                        "date": record.date_proccess,
                        "journal_id": record.journal_id.id,
                        "ref": "",
                        "partner_id": record.partner_payroll_ids.partner_id.id,
                        # "name": "name test",
                        "glosa": '',
                        "state": "draft",
                        "line_ids": val,
                    }
                    account_move_id = record.env['account.move'].create(move_vals)
                    record.account_move_id = account_move_id.id
                    account_move_id.finalize_contributions_id = record.id
                    if account_move_id:
                        record.partner_payroll_ids.state = 'process_finalized'
                    return {
                        'name': 'Pagos de planilla',
                        'type': 'ir.actions.act_window',
                        'res_model': 'account.move',
                        'view_mode': 'form',
                        'res_id': account_move_id.id,
                        'views': [(False, 'form')],
                    }
                    # account_move_id.finalize_contributions_id = record.id

                if record.liquidation_contributions == True and record.liquidation == True and record.total_amount >= (
                        record.loan_capital_bolivianos + record.balance_interest_month_bolivianos):
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
                        val = []
                        if record.total_voluntary > 0:
                            data = (0, 0, {'account_id': record.account_voluntary_contributions.id,
                                           'debit': record.total_voluntary, 'credit': 0,
                                           # 'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.total_mandatory_contributions > 0:
                            data = (0, 0, {'account_id': record.account_mandatory_contributions.id,
                                           'debit': record.total_mandatory_contributions, 'credit': 0,
                                           # 'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.other_contributions > 0:
                            data = (0, 0, {'account_id': record.account_other_contributions.id,
                                           'debit': record.other_contributions, 'credit': 0,
                                           # 'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.surpluses > 0:
                            data = (0, 0, {'account_id': record.account_surpluses.id,
                                           'debit': record.surpluses, 'credit': 0,
                                           # 'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.loan_capital_bolivianos > 0:
                            data = (0, 0, {'account_id': record.account_capital_loan.id,
                                           'debit': 0, 'credit': record.loan_capital_bolivianos,
                                           'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.balance_interest_month_bolivianos > 0:
                            data = (0, 0, {'account_id': record.account_interest_month.id,
                                           'debit': 0, 'credit': record.balance_interest_month_bolivianos,
                                           'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.disengagement > 0:
                            data = (0, 0, {'account_id': record.account_disengagement.id,
                                           'debit': 0, 'credit': record.disengagement,
                                           'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.manual_regulation_cup > 0:
                            data = (0, 0, {'account_id': record.account_regulation_cup.id,
                                           'debit': 0, 'credit': record.manual_regulation_cup,
                                           'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.manual_aporte_obligatorio > 0:
                            data = (0, 0, {'account_id': record.account_manual_aporte_obligatorio.id,
                                           'debit': 0, 'credit': record.manual_aporte_obligatorio,
                                           'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.manual_post_mortem > 0:
                            data = (0, 0, {'account_id': record.account_manual_post_mortem.id,
                                           'debit': 0, 'credit': record.manual_post_mortem,
                                           'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        if record.rest_contributions > 0:
                            data = (0, 0, {'account_id': record.account_bank_rest_contributions.id,
                                           'debit': 0, 'credit': record.rest_contributions,
                                           'partner_id': record.partner_payroll_ids.partner_id.id,
                                           'amount_currency': 0
                                           })
                            val.append(data)
                        move_vals = {
                            "date": record.date_proccess,
                            "journal_id": record.journal_id.id,
                            "ref": "",
                            "partner_id": record.partner_payroll_ids.partner_id.id,
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
                            finalized_loan.accounting_finalized_loan_id = account_move_id.id
                            record.loan_application_ids.loan_payment_ids.filtered(
                                lambda x: x.name == 'LIQUID 1').account_move_id = account_move_id.id
                            record.partner_payroll_ids.state = 'process_finalized'
                            record.state = 'done'
                        return {
                            'name': 'Pagos de planilla',
                            'type': 'ir.actions.act_window',
                            'res_model': 'account.move',
                            'view_mode': 'form',
                            'res_id': account_move_id.id,
                            'views': [(False, 'form')],
                        }


                if record.total_partial_devolution > 0 and record.liquidation == False:
                    vals = {
                        'partner_payroll_id': record.partner_payroll_ids.id,
                        'income': 0,
                        'income_passive': 0,
                        'miscellaneous_income': 0,
                        'regulation_cup': 0,
                        'mandatory_contribution_certificate': 0,
                        'voluntary_contribution_certificate': record.total_partial_devolution,
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
                        val = []
                        data = (0, 0, {'account_id': record.account_voluntary_contributions.id,
                                       'debit': record.discount_contribution, 'credit': 0,
                                       'partner_id': record.partner_payroll_ids.partner_id.id,
                                       'amount_currency': 0
                                       })
                        val.append(data)
                        data = (0, 0, {'account_id': record.account_bank_rest_contributions.id,
                                       'debit': 0, 'credit': record.rest_contributions,
                                       'partner_id': record.partner_payroll_ids.partner_id.id,
                                       'amount_currency': 0
                                       })
                        val.append(data)
                        move_vals = {
                            "date": record.date_proccess,
                            "journal_id": record.journal_id.id,
                            "ref": "",
                            "partner_id": record.partner_payroll_ids.partner_id.id,
                            # "name": "name test",
                            "glosa": '',
                            "state": "draft",
                            "line_ids": val,
                        }
                        account_move_id = record.env['account.move'].create(move_vals)
                        record.account_move_id = account_move_id.id
                        payroll.account_move_id = account_move_id.id
                        account_move_id.finalize_contributions_id = record.id
                        record.state = 'done'
                        return {
                            'name': 'Pagos de planilla',
                            'type': 'ir.actions.act_window',
                            'res_model': 'account.move',
                            'view_mode': 'form',
                            'res_id': account_move_id.id,
                            'views': [(False, 'form')],
                        }

                if record.total_partial_devolution > 0 and record.liquidation == True:
                    vals = {
                        'partner_payroll_id': record.partner_payroll_ids.id,
                        'income': 0,
                        'income_passive': 0,
                        'miscellaneous_income': 0,
                        'regulation_cup': 0,
                        'mandatory_contribution_certificate': 0,
                        'voluntary_contribution_certificate': record.total_partial_devolution,
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
                        val = []
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
                        data = (0, 0, {'account_id': record.account_bank_rest.id,
                                       'debit': 0, 'credit': record.total_diference_contribution_loan,
                                       'partner_id': record.partner_payroll_ids.partner_id.id,
                                       'amount_currency': 0
                                       })
                        val.append(data)
                        move_vals = {
                            "date": record.date_proccess,
                            "journal_id": record.journal_id.id,
                            "ref": "",
                            "partner_id": record.partner_payroll_ids.partner_id.id,
                            # "name": "name test",
                            "glosa": '',
                            "state": "draft",
                            "line_ids": val,
                        }
                        account_move_id = record.env['account.move'].create(move_vals)
                        record.account_move_id = account_move_id.id
                        payroll.account_move_id = account_move_id.id
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
                            finalized_loan.accounting_finalized_loan_id = account_move_id.id
                            record.loan_application_ids.loan_payment_ids.filtered(
                                lambda x: x.name == 'LIQUID 1').account_move_id = account_move_id.id
                            record.state = 'done'

                        return {
                            'name': 'Pagos de planilla',
                            'type': 'ir.actions.act_window',
                            'res_model': 'account.move',
                            'view_mode': 'form',
                            'res_id': account_move_id.id,
                            'views': [(False, 'form')],
                        }

    @api.depends('total_amount')
    def _compute_literal_number(self):
        for record in self:
            record.literal_number = num2words(int(record.total_amount), lang='es').upper()
            decimal = str(round(record.total_amount % 1 * 100))
            record.literal_number = record.literal_number + ', CON ' + decimal + '/100 BOLIVIANOS'





