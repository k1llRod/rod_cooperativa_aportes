from odoo import api, fields, models, _

class ReportCategoryB(models.AbstractModel):
    _name = 'report.rod_cooperativa_aportes.report_category_a'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard_record):
        # 1. Obtener registros de socios en Servicio Pasivo Categoría A
        partner_payroll = self.env['partner.payroll'].search([
            ('partner_status_especific', '=', 'passive_reserve_a'),
            ('state', '=', 'process')
        ], order='partner_id')

        sheet = workbook.add_worksheet('Detalle de Saldos Debe')

        # 2. Definición de Formatos Estilizados
        title_style = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 13, 'bg_color': '#4F81BD', 'font_color': 'white'
        })
        header_style = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'bg_color': '#D9E1F2'
        })
        text_style = workbook.add_format({'border': 1, 'align': 'left'})
        num_style = workbook.add_format({'border': 1, 'align': 'right', 'num_format': '#,##0.00'})
        center_style = workbook.add_format({'border': 1, 'align': 'center'})

        # Estilo para separar los datos de un socio de otro
        separator_style = workbook.add_format({'top': 5, 'top_color': '#4F81BD'})

        # 3. Encabezados Principales del Reporte
        sheet.merge_range('A1:F1', 'COOPERATIVA DE AHORRO Y CRÉDITO DE VÍNCULO LABORAL "COA" R.L.', title_style)
        sheet.merge_range('A2:F2', 'RELACIÓN HISTÓRICA DE DEUDAS - PASIVOS CATEGORÍA A',
                          workbook.add_format({'bold': True, 'align': 'center'}))

        # 4. Cabeceras de la Tabla de Datos (Estructura idéntica a la grilla de la imagen)
        row = 4
        headers = ['N°', 'Nombre del Socio', 'Gestión', 'Periodo', 'Referencia / Pago', 'Monto Debe (Bs)']
        for col_idx, header_text in enumerate(headers):
            sheet.write(row, col_idx, header_text, header_style)

        # 5. Iteración y Volcado Lineal de Información
        row += 1
        counter = 1

        for partner in partner_payroll:
            # Forzar la actualización del socio para consolidar montos
            partner.compute_updated_partner()

            # Si el socio no registra deudas en la subtabla, saltamos al siguiente
            if not partner.due_payments_ids:
                continue

            # Ordenamos las deudas del socio de forma cronológica por gestión y periodo
            sorted_dues = sorted(partner.due_payments_ids, key=lambda d: (d.name or 0, d.name or ''))

            for due in sorted_dues:
                sheet.write(row, 0, counter, center_style)
                sheet.write(row, 1, partner.partner_id.name or '', text_style)

                # Campo Periodo (ej: "04/2026") y Gestión (ej: 2026)
                sheet.write(row, 2, due.gestion or '', center_style)
                sheet.write(row, 3, due.name or '', center_style)


                # Identificador o Glosa del pago adelantado/programado
                sheet.write(row, 4, due.name or 'COAAPOR0606', text_style)

                # Monto total adeudado del registro mensual (Total debe)
                monto_debe = due.d_total if hasattr(due, 'd_total') else due.amount or 0.0
                sheet.write(row, 5, monto_debe or 0.0, num_style)

                row += 1
                counter += 1

            # Agregamos una sutil línea divisoria inferior al terminar los registros de cada socio
            for col in range(6):
                sheet.write(row, col, '', separator_style)
            row += 1

        # 6. Ajuste y Dimensionamiento de las Columnas
        sheet.set_column('A:A', 6)  # Contador N°
        sheet.set_column('B:B', 40)  # Nombre del Socio
        sheet.set_column('C:E', 16)  # Periodo, Gestión y Referencia
        sheet.set_column('F:F', 18)  # Monto Total Debe
