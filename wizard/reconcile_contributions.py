from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class ReconcileContributions(models.TransientModel):
    _name = 'reconcile.contributions'
    _description = 'Conciliar pagos de aportes'

    date_payment = fields.Date(string="Fecha de pago", require=True, default=fields.Date.today())
    date_field_select = fields.Date(string="Fecha periodo", require=True, default=fields.Date.today() - relativedelta(months=1))
    month = fields.Char(string="Mes", compute="compute_date_format")
    year = fields.Char(string="Año", compute="compute_date_format")
    reconcile_records = fields.Integer(string="Registros para conciliar", readonly=True)
    drawback = fields.Boolean(string="Reintegro", default=False)
    months = fields.Many2many('month', string="Meses")
    correct_registry = fields.Integer(string="Corregir registros", readonly=True)
    reconciled_records = fields.Integer(string="Registros conciliados", readonly=True)
    outstanding_payments = fields.Integer(string="Pagos pendientes", compute='onchange_partner_status_especific',readonly=True)
    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),
                                                 ('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado')

    @api.depends('date_field_select')
    def compute_date_format(self):
        for record in self:
            if record.date_field_select == False:
                record.year = 'Seleccionar fecha'
                record.month = 'Seleccionar fecha'
            else:
                record.month = record.date_field_select.strftime('%m')
                record.year = record.date_field_select.strftime('%Y')
                period = record.month + '/' + record.year
                record.reconcile_records = len(self.env['nominal.relationship.mindef.contributions'].search(
                    [('period_process', '=', period), ('state', '=', 'draft')]))
                record.correct_registry = len(self.env['nominal.relationship.mindef.contributions'].search(
                    [('period_process', '=', period), ('state', '=', 'no_reconciled')]))
                record.reconciled_records = len(self.env['nominal.relationship.mindef.contributions'].search(
                    [('period_process', '=', period), ('state', '=', 'reconciled')]))

    @api.depends('partner_status_especific')
    def onchange_partner_status_especific(self):
        if self.partner_status_especific:
            self.outstanding_payments = len(self.env['partner.payroll'].search(
                [('outstanding_payments', '>', '0'), ('state', '=', 'process'),
                 ('partner_status_especific', '=', self.partner_status_especific)]))
        else:
            self.outstanding_payments = len(self.env['partner.payroll'].search(
                [('outstanding_payments', '>', '0'), ('state', '=', 'process')]))

    def action_reconcile(self):
        # Acción para conciliar los pagos de aportes
        miscellaneous_income = float(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.miscellaneous_income'))
        mandatory_contribution_certificate = self.env['ir.config_parameter'].sudo().get_param(
            'rod_cooperativa_aportes.mandatory_contribution_certificate')
        period = self.month + '/' + self.year
        filing_cabinet_ids = self.env['nominal.relationship.mindef.contributions'].search(
            [('period_process', '=', period), ('state', '=', 'draft')])
        partner_payroll_ids = self.env['partner.payroll'].search(
            ['|', ('state', '=', 'process'), ('partner_status_especific', '=', 'active_service')])

        status_dinamic = 'ministry_defense'
        if self.drawback == True:
            status_dinamic = 'drawback'
        for partner in partner_payroll_ids:
            search_partner = filing_cabinet_ids.filtered(lambda x: x.eit_item == partner.partner_id.code_contact)
            if search_partner:
                if len(partner.payroll_payments_ids) == 0:
                    val = {'partner_payroll_id': partner.id,
                           'payment_date': self.date_payment,
                           'date_pivote': self.date_field_select,
                           'income': search_partner.amount_bs,
                           'income_passive': 0,
                           'drawback': self.drawback}
                else:
                    val = {'partner_payroll_id': partner.id,
                           'payment_date': self.date_payment,
                           'date_pivote': self.date_field_select,
                           'income': search_partner.amount_bs,
                           'income_passive': 0,
                           'drawback': self.drawback}
                mo = self.env['payroll.payments'].create(val)
                partner_id = self.env['res.partner'].search([('id', '=', partner.partner_id.id)])
                partner_id.city = search_partner.distribution
                if self.drawback == True: mo.onchange_drawback()
                mo.ministry_defense()
                mo.onchange_income()
                if self.drawback == True:
                    list = ''
                    for rec in self.months:
                        list = rec.name + ',' + list
                    partner.message_post(body="Reintegro: " + list)
                    mo.message_post(body="Reintegro: " + list)

                search_partner.date_process = self.date_field_select
                search_partner.state = 'reconciled'
                search_partner.period_process = self.month + '/' + self.year
            else:
                if len(partner.payroll_payments_ids) > 0 and partner.date_burn_partner != False:
                    val = {'partner_payroll_id': partner.id,
                           'payment_date': self.date_payment,
                           'date_pivote': self.date_field_select,
                           'income': search_partner.amount_bs,
                           'income_passive': 0,
                           'drawback': self.drawback}
                    mo = self.env['payroll.payments'].create(val)
                    mo.no_contribution()


        array_no_reconciled = filing_cabinet_ids.filtered(lambda x: x.period_process == period and x.state == 'draft')
        no_reconciled = len(array_no_reconciled)
        for rec in array_no_reconciled:
            rec.write({'state': 'no_reconciled'})
            rec.write({'period_process': self.month + '/' + self.year})
            rec.write({'date_process': self.date_field_select})

        context = {'default_message': 'Se han conciliado ' + str(
            len(filing_cabinet_ids) - no_reconciled) + ' registros de ' + str(len(filing_cabinet_ids))}
        return {
            'name': 'Registros conciliados',
            'type': 'ir.actions.act_window',
            'res_model': 'alert.message',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }

    def compute_reconcile_records(self):
        for record in self:
            record.correct_registry = len(record.env['nominal.relationship.mindef.contributions'].search(
                [('period_process', '=', record.month + '/' + record.year), ('state', '=', 'reconc')]))

    def register_missing_payments(self):
        for record in self:
            record.env['nominal.relationship.mindef.contributions'].search(
                [('period_process', '=', record.month + '/' + record.year), ('state', '=','reconc')]).write({'state': 'draft'})