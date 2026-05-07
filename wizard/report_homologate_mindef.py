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

    @api.onchange('month', 'year')
    def _onchange_month_year(self):
        if self.month and self.year:
            period = f"{self.month}/{self.year}"
            contributions = self.env['nominal.relationship.mindef.contributions'].search([
                ('period_process', '=', period)
            ])
            self.draft_quantity = len(contributions.filtered(lambda x: x.state == 'draft'))
            self.no_reconciled_quantity = len(contributions.filtered(lambda x: x.state == 'no_reconciled'))
            self.reconciled_quantity = len(contributions.filtered(lambda x: x.state == 'reconciled'))
            self.observed_quantity = len(contributions.filtered(lambda x: x.state == 'observed'))
        else:
            self.draft_quantity = 0
            self.no_reconciled_quantity = 0
            self.reconciled_quantity = 0
            self.observed_quantity = 0

    def action_generate_summary(self):
        self.ensure_one()
        period = f"{self.month}/{self.year}"

        # Buscamos todas las contribuciones del periodo
        contributions = self.env['nominal.relationship.mindef.contributions'].search([
            ('period_process', '=', period)
        ])

        # Preparamos los datos para el reporte
        # Pasamos los IDs de los registros separados por estado para facilitar el dibujo en Excel
        summary_data = {
            'period': period,
            'date': fields.Datetime.now().strftime('%d/%m/%Y %H:%M'),
            'stats': {
                'draft': len(contributions.filtered(lambda x: x.state == 'draft')),
                'no_reconciled': len(contributions.filtered(lambda x: x.state == 'no_reconciled')),
                'reconciled': len(contributions.filtered(lambda x: x.state == 'reconciled')),
                'observed': len(contributions.filtered(lambda x: x.state == 'observed')),
            },
            # Pasamos los IDs de los registros para que el reporte los lea
            'ids_draft': contributions.filtered(lambda x: x.state == 'draft').ids,
            'ids_no_reconciled': contributions.filtered(lambda x: x.state == 'no_reconciled').ids,
            'ids_reconciled': contributions.filtered(lambda x: x.state == 'reconciled').ids,
            'ids_observed': contributions.filtered(lambda x: x.state == 'observed').ids,
        }

        return self.env.ref('rod_cooperativa_aportes.action_report_mindef_xlsx').report_action(self, data=summary_data)

