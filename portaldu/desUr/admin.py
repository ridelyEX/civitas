from django.contrib import admin
from .models import Uuid, data, SubirDocs, Pagos, soli, Files, Licitaciones
from portaldu.cmin.models import Users, LoginDate

# Los modelos de usuario ya están administrados por cmin
# Solo agregamos admin para los modelos específicos de DesUr

@admin.register(Uuid)
class UuidAdmin(admin.ModelAdmin):
    list_display = ('prime', 'uuid')
    readonly_fields = ('uuid',)

@admin.register(data)
class DataAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pApe', 'mApe', 'bDay', 'tel', 'asunto')
    list_filter = ('bDay', 'sexo', 'asunto')
    search_fields = ('nombre', 'pApe', 'mApe', 'curp', 'tel')

@admin.register(SubirDocs)
class SubirDocsAdmin(admin.ModelAdmin):
    list_display = ('nomDoc', 'descDoc', 'fechaDoc')
    list_filter = ('fechaDoc',)
    search_fields = ('nomDoc', 'descDoc')

@admin.register(Pagos)
class PagosAdmin(admin.ModelAdmin):
    list_display = ('pago_ID', 'data_ID', 'fecha', 'pfm')
    list_filter = ('fecha',)

@admin.register(soli)
class SoliAdmin(admin.ModelAdmin):
    list_display = ('soli_ID', 'data_ID', 'fecha', 'puo', 'folio')
    list_filter = ('fecha', 'puo')
    search_fields = ('folio', 'puo')

@admin.register(Files)
class FilesAdmin(admin.ModelAdmin):
    list_display = ('fDoc_ID', 'nomDoc', 'soli_FK')
    search_fields = ('nomDoc',)


admin.site.register(Licitaciones)
