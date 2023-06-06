from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


class ReconcileContributions(models.TransientModel):
    _name = 'reconcile.contributions'
    _description = 'Conciliar pagos de aportes'

    date_field_select = fields.Date(string="Fecha", require=True, default=fields.Date.today())
    month = fields.Char(string="Mes", compute="compute_date_format")
    year = fields.Char(string="Año", compute="compute_date_format")
    reconcile_records = fields.Integer(string="Registros para conciliar", readonly=True)

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



    def action_reconcile(self):
        # Acción para conciliar los pagos de aportes
        miscellaneous_income = float(
            self.env['ir.config_parameter'].sudo().get_param('rod_cooperativa_aportes.miscellaneous_income'))
        period = self.month + '/' + self.year
        filing_cabinet_ids = self.env['nominal.relationship.mindef.contributions'].search(
            [('period_process', '=', period),('state','=','draft')])
        partner_payroll_ids = self.env['partner.payroll'].search([('state', '=', 'process')])
        for partner in partner_payroll_ids:
            search_partner = filing_cabinet_ids.filtered(lambda x: x.eit_item == partner.partner_id.code_contact)
            if search_partner:
                if partner.miscellaneous_income == miscellaneous_income:
                    partner.payroll_payments_ids = [
                        (0, 0, {'payment_date': self.date_field_select, 'income': search_partner.amount_bs,
                                'state': 'ministry_defense'})]  # Agregar el pago de aportes
                else:
                    partner.payroll_payments_ids = [
                        (0, 0, {'payment_date': self.date_field_select, 'income': search_partner.amount_bs,
                                'state': 'ministry_defense',
                                'miscellaneous_income': miscellaneous_income - partner.miscellaneous_income})]  # Agregar el pago de a

                search_partner.date_process = self.date_field_select
                search_partner.state = 'reconciled'
                search_partner.period_process = self.month+'/'+self.year

            no_reconciled = len(filing_cabinet_ids.filtered(lambda x: x.period_process == False))
            array_no_reconciled = self.env['nominal.relationship.mindef.contributions'].search([('period_process','=',False)])
            for rec in array_no_reconciled:
                rec.write({'state': 'no_reconciled'})
                rec.write({'period_process': self.month+'/'+self.year})
                rec.write({'date_process': self.date_field_select})
        context = {'default_message': 'Se han conciliado '+ str(len(filing_cabinet_ids)-no_reconciled) + ' registros de '+ str(len(filing_cabinet_ids))}
        return {
            'name': 'Registros conciliados',
            'type': 'ir.actions.act_window',
            'res_model': 'alert.message',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }

        # raise UserError(_('Se han conciliado %s registros de %s') % (len(filing_cabinet_ids)-no_reconciled, len(filing_cabinet_ids)))


    # @api.depends('date_field_select')
    # def compute_reconcile_records(self):
    #     self.reconcile_records =


