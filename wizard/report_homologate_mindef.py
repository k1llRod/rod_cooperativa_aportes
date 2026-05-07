from odoo import models, fields, api


class MindefReportWizard(models.TransientModel):
    _name = 'mindef.report.wizard'
    _description = 'Asistente para Resumen Mindef'

    month = fields.Selection([
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'),
        ('04', 'Abril'), ('05', 'Mayo'), ('06', 'Junio'),
        ('07', 'Julio'), ('08', 'Agosto'), ('09', 'Septiembre'),
        ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ], string='Mes', required=True)
    year = fields.Char(string='Año', default=lambda self: str(fields.Date.today().year), required=True)

    draft_quantity = fields.Integer(string='Contador en borrador')
    no_reconciled_quantity = fields.Integer(string='Contador no conciliado')
    reconciled_quantity = fields.Integer(string='Contador conciliado')
    observed_quantity = fields.Integer(string='Contador observado')



    def action_generate_summary(self):
        period = f"{self.month}/{self.year}"

        # Consultar los datos en el modelo nominal.relationship.mindef.contributions
        contributions = self.env['nominal.relationship.mindef.contributions'].search([
            ('period_process', '=', period)
        ])

        # Procesar contadores por estado
        summary_data = {
            'period': period,
            'draft_quantity': len(contributions.filtered(lambda x: x.state == 'draft')),
            'no_reconciled_quantity': len(contributions.filtered(lambda x: x.state == 'no_reconciled')),
            'reconciled_quantity': len(contributions.filtered(lambda x: x.state == 'reconciled')),
            'observed_quantity': len(contributions.filtered(lambda x: x.state == 'observed')),
            'date': fields.Datetime.now(),
        }

        # Crear el registro en el modelo de reporte
        report_rec = self.env['report.homologate.mindef'].create(summary_data)

        # Retornar la vista del reporte generado
        return {
            'name': 'Resumen de Homologación',
            'type': 'ir.actions.act_window',
            'res_model': 'report.homologate.mindef',
            'view_mode': 'form',
            'res_id': report_rec.id,
            'target': 'current',
        }

