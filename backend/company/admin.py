from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from django.core.mail import get_connection, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.shortcuts import HttpResponseRedirect
from zipfile import ZipFile
from os.path import basename
from company.models import CompanyPerson, CompanyProfile, InternshipAdvertisement, InternshipOffer, JobOffer, JobAdvertisement
from .resources import CompanyPersonResource
from .resources import InternshipAdvertisementResource, InternshipOfferResource, JobAdvertisementResource, JobOfferResource
import csv
from django.http import HttpResponse


class JobAdvertisementInline(admin.StackedInline):
    model = JobAdvertisement


class InternshipAdvertisementInline(admin.StackedInline):
    model = InternshipAdvertisement


class JobOfferInline(admin.StackedInline):
    model = JobOffer


class InternshipOfferInline(admin.StackedInline):
    model = InternshipOffer


class CompanyPersonInline(admin.StackedInline):
    model = CompanyPerson


def export_as_csv(modeladmin, request, queryset):

    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in queryset:
        _ = writer.writerow([getattr(obj, field) for field in field_names])

    return response


def get_zipped_resumes_for_ad(modeladmin, request, queryset):
    if queryset.count() != 1:
        messages.info(request, "Can not export more than one object to zip at once.")
        return
    if modeladmin.model is JobAdvertisement:
        offers = JobOffer.objects.filter(profile__in=queryset).all()
    elif modeladmin.model is InternshipAdvertisement:
        offers = InternshipOffer.objects.filter(profile__in=queryset).all()
    if not offers.count():
        messages.warning(request, "No offers exist for this advertisement")
        return

    zip_path = "assets/media/resume/zipped/" + offers[0].profile.company.name.replace(" ", "_") + '_' + offers[0].profile.designation.replace(
        " ", "_") + '_' + str(offers[0].profile_id) + ".zip"

    missing = []
    for offer in offers:
        if not offer.resume:
            missing.append(offer.student.user.first_name+" "+offer.student.user.last_name+"("+offer.student.roll_no+")")

    if missing:
        messages.error(request, 'Missing Resume of '+', '.join(missing)+" .")
        return
    else:
        zip = ZipFile(zip_path, 'w')
        for offer in offers:
            zip.write(offer.resume.file.path, basename(offer.resume.file.path))

        zip.close()
        url = "/media/resume/zipped/" + offers[0].profile.company.name.replace(" ", "_") + '_' + offers[0].profile.designation.replace(
            " ", "_") + '_' + str(offers[0].profile_id) + ".zip"
        return HttpResponseRedirect(url)


def get_zipped_resumes(modeladmin, request, queryset):
    if modeladmin.model is JobOffer:
        offers = queryset
    elif modeladmin.model is InternshipOffer:
        offers = queryset
    if not offers.count():
        messages.warning(request, "Select atleast 1 offer")
        return

    zip_path = "assets/media/resume/zipped/" + offers[0].profile.company.name.replace(" ", "_") + '_' + offers[0].profile.designation.replace(
        " ", "_") + '_' + str(offers[0].profile_id) + ".zip"

    missing = []
    for offer in offers:
        if not offer.resume:
            missing.append(offer.student.user.first_name+" "+offer.student.user.last_name+"("+offer.student.roll_no+")")

    if missing:
        messages.error(request, 'Missing Resume of '+', '.join(missing)+" .")
        return
    else:
        zip = ZipFile(zip_path, 'w')
        for offer in offers:
            zip.write(offer.resume.file.path, basename(offer.resume.file.path))
        zip.close()
        url = "/media/resume/zipped/" + offers[0].profile.company.name.replace(" ", "_") + '_' + offers[0].profile.designation.replace(
            " ", "_") + '_' + str(offers[0].profile_id) + ".zip"
        return HttpResponseRedirect(url)


def make_active(modeladmin, request, queryset):
    queryset.update(active=True)


def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


def show_company(modeladmin, request, queryset):
    queryset.update(show_company=True)


def hide_company(modeladmin, request, queryset):
    queryset.update(show_company=False)


def mark_placed(modeladmin, request, queryset):
    queryset.update(is_accepted=True)


def mark_ppo(modeladmin, request, queryset):
    queryset.update(ppo=True)
    queryset.update(is_accepted=True)


def mark_accepted(modeladmin, request, queryset):
    queryset.update(is_accepted=True)


def send_email(self, request, obj, subject):
    if "_sendemail" in request.POST:
        obj.email_sent = True
        obj.save()
        from_email = settings.SERVER_EMAIL
        try:
            mtech_stipend = obj.mtech_stipend
        except AttributeError:
            mtech_stipend = False
        with get_connection(
                username=from_email,
                password=settings.SERVER_EMAIL_PASSWORD
        ) as connection:
            to_email = []
            for email_id in obj.email_ids.filter(category="Advertisement Recipient"):
                to_email.append(email_id.email)
            html_content = render_to_string("company/advertisement_email.html", {'subject': subject,
                                                                                 'company': obj.company,
                                                                                 'designation': obj.designation,
                                                                                 'description': obj.description,
                                                                                 'description_file': (obj.description_file if obj.description_file
                                                                                                      else False),
                                                                                 'tentative_join_date': obj.tentative_join_date,
                                                                                 'tentative_job_location': obj.tentative_job_location,
                                                                                 'ctc': obj.ctc,
                                                                                 'gross_salary': obj.gross_salary if obj.gross_salary else False,
                                                                                 'bonus': obj.bonus if obj.bonus else False,
                                                                                 'bond': obj.bond if obj.bond else False,
                                                                                 'bond_details': obj.bond_details if obj.bond_details else False,
                                                                                 'eligible_program_branch': obj.eligible_program_branch,
                                                                                 'mtech_stipend': mtech_stipend,
                                                                                 'resume_required': obj.resume_required,
                                                                                 'aptitude_test_required': obj.aptitude_test_required,
                                                                                 'group_discussion_required': obj.group_discussion_required,
                                                                                 'number_of_technical_interviews': obj.number_of_technical_interviews,
                                                                                 'number_of_technical_tests': obj.number_of_technical_tests,
                                                                                 'number_of_hr_rounds': obj.number_of_hr_rounds,
                                                                                 'min_gpa': obj.min_gpa if obj.min_gpa else False,
                                                                                 'min_ug_gpa': obj.min_ug_gpa if obj.min_ug_gpa else False,
                                                                                 'other_details': obj.other_details if obj.other_details else False,
                                                                                 'expiry': obj.expiry})
            text_content = strip_tags(html_content)
            message = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=to_email,
                                             connection=connection)
            message.attach_alternative(html_content, "text/html")
            message.send()
        self.message_user(request, "Email Sent")
        return HttpResponseRedirect(".")


@admin.register(CompanyProfile)
class CompanyProfileAdmin(ImportExportActionModelAdmin):
    """ readonly_fields = ['registration_timestamp', ]
    resource_class = CompanyProfileResource
    inlines = (CompanyPersonInline, JobOfferInline, InternshipOfferInline,)
    list_display = ['name', 'domain', 'url', 'registration_timestamp']
    list_filter = ['domain', 'registration_timestamp']
    search_fields = ['name', 'user__username']
 """
    class Meta:
        model = CompanyProfile
        fields = '__all__'


@admin.register(CompanyPerson)
class CompanyPersonAdmin(ImportExportActionModelAdmin):
    resource_class = CompanyPersonResource
    list_display = ['name', 'designation', 'company', 'company_domain', 'phone', 'email']
    list_filter = ['company', 'designation']
    search_fields = ['name', 'company', 'designation']

    def company_domain(self, instance):
        return instance.company.domain

    class Meta:
        model = CompanyPerson
        fields = '__all__'


@admin.register(JobAdvertisement)
class JobAdvertisementAdmin(ImportExportActionModelAdmin):
    change_form_template = "admin/send_advertisement.html"
    readonly_fields = ['creation_timestamp', ]
    resource_class = JobAdvertisementResource
    list_display = ['company', 'designation', 'ctc', 'min_gpa', 'active', 'show_company', 'expiry', 'email_sent', 'only_female']
    list_filter = ['active', 'show_company', 'creation_timestamp', 'only_female', 'company']
    ordering = ['company']
    search_fields = ['company__name', ]
    actions = [get_zipped_resumes_for_ad, make_active, make_inactive, show_company, hide_company, export_as_csv]

    def response_change(self, request, obj):
        subject = "Job Advertisement"
        send_email(self, request, obj, subject)
        return super().response_change(request, obj)

    class Meta:
        model = JobAdvertisement
        fields = '__all__'


@admin.register(InternshipAdvertisement)
class InternshipAdvertisementAdmin(ImportExportActionModelAdmin):
    change_form_template = "admin/send_advertisement.html"
    readonly_fields = ['creation_timestamp', ]
    resource_class = InternshipAdvertisementResource
    list_display = ['company', 'designation', 'min_gpa', 'ctc', 'active', 'show_company', 'expiry', 'email_sent', 'only_female']
    list_filter = ['company', 'active', 'show_company', 'creation_timestamp', 'only_female']
    ordering = ['company']
    search_fields = ['company__name', ]
    actions = [get_zipped_resumes_for_ad, make_active, make_inactive, show_company, hide_company, export_as_csv]

    def response_change(self, request, obj):
        subject = "Internship Advertisement"
        send_email(self, request, obj, subject)
        return super().response_change(request, obj)

    class Meta:
        model = InternshipAdvertisement
        fields = '__all__'


@admin.register(InternshipOffer)
class InternshipOfferAdmin(ImportExportActionModelAdmin):
    readonly_fields = ['application_timestamp', ]
    resource_class = InternshipOfferResource
    list_display = ['student', 'get_roll_no', 'company', 'profile', 'is_accepted', 'get_file']
    list_filter = ['company', 'is_accepted', 'profile']
    ordering = ['student']
    search_fields = ['company__name', 'student__user__username', 'student__user__first_name',
                     'student__user__last_name', 'student__roll_no']
    ImportExportActionModelAdmin.actions = ImportExportActionModelAdmin.actions + [get_zipped_resumes, mark_placed, mark_ppo, mark_accepted]

    class Meta:
        model = InternshipOffer
        fields = '__all__'


@admin.register(JobOffer)
class JobOfferAdmin(ImportExportActionModelAdmin):
    readonly_fields = ['application_timestamp', ]
    resource_class = JobOfferResource
    list_display = ['student', 'get_roll_no', 'company', 'profile', 'is_accepted', 'get_file']
    list_filter = ['company', 'is_accepted', 'profile']
    ordering = ['student']
    search_fields = ['company__name', 'student__user__username', 'student__user__first_name',
                     'student__user__last_name', 'student__roll_no']
    ImportExportActionModelAdmin.actions = ImportExportActionModelAdmin.actions

    class Meta:
        model = JobOffer
        fields = '__all__'
