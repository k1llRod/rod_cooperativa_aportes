from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re
from dateutil.relativedelta import relativedelta


class WizardPayroll(models.TransientModel):
    _name = 'wizard.payroll.payments'
    # Campos del wizard
    account_move_id = fields.Many2one('account.move', string='Asiento contable')
    name = fields.Char(string='ID aporte')
    date = fields.Date(string='Fecha', default=fields.Datetime.now())
    period = fields.Char(string='Periodo')
    state = fields.Selection(
        [('draft', 'Borrador'), ('transfer', 'Transferencia bancaria'), ('ministry_defense', 'Ministerio de defensa'),
         ('contribution_interest', 'Aporte y rendimiento COAA'),
         ('no_contribution', 'Sin aporte'),
         ('capital_initial', 'Capital inicial')],
        default='ministry_defense', string='Estado')
    account_journal_id = fields.Many2one('account.journal', string='Diario')
    payment_date = fields.Date(string='Fecha de pago')
    amount_total = fields.Float(string='Monto total')
    amount_total_contributions = fields.Float(string='Monto total de aportes')
    account_income_id = fields.Many2one('account.account', string='Cuenta de ingreso')
    account_inscription_id = fields.Many2one('account.account', string='Cuenta de inscripción')
    account_regulation_cup_id = fields.Many2one('account.account', string='Cuenta de regulación de taza')
    account_mandatory_contribution_id = fields.Many2one('account.account', string='Cuenta de aporte obligatorio')
    account_voluntary_contribution_id = fields.Many2one('account.account', string='Cuenta de aporte voluntario')
    total_income = fields.Float(string='Total de ingresos')
    total_miscellaneous_income = fields.Float(string='Total de ingresos varios')
    total_regulation_cup = fields.Float(string='Total de regulación de taza')
    total_mandatory_contribution = fields.Float(string='Total de aporte obligatorio')
    total_voluntary_contribution = fields.Float(string='Total de aporte voluntario')
    val = fields.Many2many('payroll.payments', string='Pagos')
    def action_confirm(self):
        move_line = []
        reference = 'APORTES ' + self.period + self.val[0].partner_name
        for record in self:
            journal_id = record.account_journal_id
            # for rec in self.val:
            #     total_income = rec.income if rec.income != 0 else rec.income_passive
            #     data = (0, 0,{
            #         'account_id': record.account_income_id.id,
            #         'name': rec.name,
            #         'debit': total_income if total_income > 0 else 0,
            #         'credit': 0
            #     })
            #     if not (record.total_income == 0): move_line.append(data)
            total_income = record.total_income
            data = (0, 0, {
                'account_id': record.account_income_id.id,
                'name': record.name,
                'debit': total_income if total_income > 0 else 0,
                'credit': 0
            })
            if not (record.total_income == 0): move_line.append(data)
            # data = (0, 0,{
            #         'account_id': record.account_income_id.id,
            #         'name': record.name,
            #         'debit': record.total_income if record.total_income > 0 else 0,
            #         'credit': 0
            # })

            data = (0, 0, {
                    'account_id': record.account_inscription_id.id,
                    'name': record.name,
                    'debit': 0,
                    'credit': record.total_miscellaneous_income,
            })
            if not (record.total_miscellaneous_income == 0): move_line.append(data)
            data = (0, 0, {
                    'account_id': record.account_regulation_cup_id.id,
                    'name': record.name,
                    'debit': 0,
                    'credit': record.total_regulation_cup,
            })
            if not (record.total_regulation_cup == 0): move_line.append(data)
            data = (0, 0, {
                    'account_id': record.account_mandatory_contribution_id.id,
                    'name': record.name,
                    'debit': 0,
                    'credit': record.total_mandatory_contribution,
            })
            if not (record.total_mandatory_contribution == 0): move_line.append(data)
            data = (0, 0, {
                    'account_id': record.account_voluntary_contribution_id.id,
                    'name': record.name,
                    'debit': 0,
                    'credit': record.total_voluntary_contribution,
            })
            if not (record.total_voluntary_contribution == 0): move_line.append(data)
        move_vals = {
            "date": record.payment_date,
            "journal_id": journal_id.id,
            "ref": reference,
            # "company_id": payment.company_id.id,
            # "name": "name test",
            "state": "draft",
            "line_ids": move_line,
        }
        account_move_id = record.env['account.move'].create(move_vals)
        account_move_id.payroll_payment_ids = record.val
        self.account_move_id.unlink()
        search_payments = self.val
        for payment in search_payments:
            payment.write({'account_move_id': account_move_id.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': account_move_id.id,
            'views': [(False, 'form')],
        }



