from company.serializers import InternshipAdvertisementSerializer, InternshipOfferSerializer, JobAdvertisementSerializer, JobOfferSerializer
from django.shortcuts import get_object_or_404
from main.models import OfficeMails
from company.models import InternshipAdvertisement, InternshipOffer, JobAdvertisement, JobOffer
from cdc_portal.utils import get_config_value
from django.db.utils import IntegrityError
from rest_framework.response import Response
from .serializers import ProgramAndBranchSerializer, StudentProfileSerializer, ResumeSerializer
from .models import StudentProfile, Resume, ProgramAndBranch
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class StudentDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def get_data_from_rollno(self, roll):
        import re
        dic = {}
        lis1 = re.split("\d+", roll)  # noqa: W605
        lis2 = re.split("\D+", roll)  # noqa: W605
        try:
            dic["RollNo"], dic["Year"], dic["Batch"], dic["Branch"] = lis2[-1], lis2[-2], lis1[0], lis1[1]
        except:  # noqa: E722
            dic["RollNo"], dic["Year"], dic["Batch"], dic["Branch"] = -1, 20, 'M', 'CS'
        return dic

    def post(self, request, *args, **kwargs):
        data = {}
        for key in request.data.keys():
            if request.data.get(key) != '':
                if request.data.get(key) == 'true':
                    data[key] = True
                elif request.data.get(key) == 'false':
                    data[key] = False
                else:
                    data[key] = request.data.get(key)
        user = request.user
        r_dic = self.get_data_from_rollno(user.username)
        data["year"] = r_dic["Year"]
        data["roll_no"] = user.username
        if r_dic["RollNo"] == -1:
            data["roll_no"] = "Unknown"
        getter = r_dic["Batch"] + '/' + r_dic["Branch"]
        program_branch = ProgramAndBranch.objects.filter(getter=getter)
        if not program_branch.exists():
            program_branch = ProgramAndBranch.objects.create(getter=getter, name="Unknown Branch" + user.username)
        else:
            program_branch = program_branch.first()
        try:
            profile = StudentProfile.objects.create(user=user, **data, program_branch=program_branch)
            profile.save()
        except IntegrityError:
            return Response({'Error': 'Invalid/Empty Fields in Form'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(StudentProfileSerializer(profile).data, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        user = request.user
        allowed_edit = get_config_value('AllowProfileEdit')
        student_profile = get_object_or_404(StudentProfile, user=user)
        # student_profile = StudentProfile.objects.get(user=user)
        serializer = StudentProfileSerializer(student_profile)
        data = serializer.data
        data['AllowedEdit'] = allowed_edit
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        data = {}
        allowed_edit = get_config_value('AllowProfileEdit')
        if not allowed_edit:
            return Response({"Error": "Edit profile is not allowed now"}, status=status.HTTP_403_FORBIDDEN)
        for key in request.data.keys():
            if request.data.get(key) != '':
                if request.data.get(key) == 'true':
                    data[key] = True
                elif request.data.get(key) == 'false':
                    data[key] = False
                else:
                    data[key] = request.data.get(key)
                    if key == 'jee_air' and request.data.get(key) == 'null':
                        data[key] = None
        user = request.user
        profile = StudentProfile.objects.get(user=user)
        serializer = StudentProfileSerializer(instance=profile, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = request.user
        profile = StudentProfile.objects.get(user=user)
        operation = profile.delete()
        data = {}
        if operation:
            data["operation status"] = "Successfully deleted user profile"
        else:
            data["operation status"] = "Failed to delete user profile"
        return Response(data=data)


class Resumes(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def get(self, request, *args, **kwargs):
        approved = request.query_params.get('approved', False)
        if not StudentProfile.objects.filter(user=request.user).exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
        if approved:
            resumes = Resume.objects.filter(student__user=request.user, is_verified=True).order_by('id')
        else:
            resumes = Resume.objects.filter(student__user=request.user).order_by('id')
            if len(resumes) == 0:
                profile = StudentProfile.objects.get(user=request.user)
                return Response(StudentProfileSerializer(profile).data, status=status.HTTP_200_OK)
        serializer = ResumeSerializer(resumes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = ResumeSerializer(data=request.data)
        if not StudentProfile.objects.filter(user=request.user).exists():
            return Response("Create a profile before Uploading Resume", status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            serializer.save(student=StudentProfile.objects.get(user=request.user))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        resume = Resume.objects.get(id=pk)
        user = request.user
        if resume.student.user.id != user.id:
            return Response({'Error': 'Cannot delete others resume'}, status.HTTP_403_FORBIDDEN)
        data = {}
        if resume.is_verified:
            return Response({'Error': 'Can not delete verified resume'}, status.HTTP_403_FORBIDDEN)
        else:
            operation = resume.delete()
            if operation:
                return Response({'Error': 'Successfully deleted resume'}, status.HTTP_200_OK)
            else:
                return Response({'Error': 'Cannot delete the resume'}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(data=data)


class AvailableOffers(APIView):
    permission_classes = (IsAuthenticated,)

    def get_applied_ad_list(self, user, model):
        if model == InternshipAdvertisement:
            m = InternshipOffer
        else:
            m = JobOffer
        return model.objects.filter(
            id__in=m.objects.filter(student__user=user).values_list('profile'))

    def get_offers(self, profile, model):
        if not profile.banned:
            if profile.program_branch.check_gpa:
                if profile.gender == 'Male':
                    offers = model.objects.filter(min_gpa__lte=profile.gpa, min_ug_gpa__lte=profile.ug_gpa,
                                                  eligible_program_branch__getter__contains=profile.program_branch.getter,
                                                  only_female=False, active=True).difference(self.get_applied_ad_list(profile.user, model))
                else:
                    offers = model.objects.filter(min_gpa__lte=profile.gpa, min_ug_gpa__lte=profile.ug_gpa,
                                                  eligible_program_branch__getter__contains=profile.program_branch.getter,
                                                  active=True).difference(self.get_applied_ad_list(profile.user, model))
            else:
                if profile.gender == 'Male':
                    offers = model.objects.filter(min_gpa__lte=profile.gpa,
                                                  eligible_program_branch__getter__contains=profile.program_branch.getter,
                                                  only_female=False, active=True).difference(self.get_applied_ad_list(profile.user, model))
                else:
                    offers = model.objects.filter(min_gpa__lte=profile.gpa,
                                                  eligible_program_branch__getter__contains=profile.program_branch.getter,
                                                  active=True).difference(self.get_applied_ad_list(profile.user, model))

            return offers

    def get(self, request):
        show = get_config_value('ShowAdertisements')
        profile = get_object_or_404(StudentProfile, user=request.user)
        IntershipYears = get_config_value('IntershipYears')
        JobYears = get_config_value('JobYears')
        if profile.banned:
            Response({'Error': 'You are Banned', }, status.HTTP_403_FORBIDDEN)
        if profile.placed:
            Response({'Error': 'You are Placed', }, status.HTTP_403_FORBIDDEN)
        year_combo = profile.program_branch.getter.split('/')[0] + str(profile.year)
        offers = {}
        if year_combo in IntershipYears:
            model = InternshipAdvertisement
            serializer = InternshipAdvertisementSerializer
            off = self.get_offers(profile, model)
            offers['Internships'] = serializer(off, many=True).data if show else []
        if year_combo in JobYears:
            model = JobAdvertisement
            serializer = JobAdvertisementSerializer
            off = self.get_offers(profile, model)
            offers['Jobs'] = serializer(off, many=True).data if show else []
        return Response(offers, status.HTTP_200_OK)


class UpcomingOffers(APIView):
    permission_classes = (IsAuthenticated,)

    def get_applied_ad_list(self, user, model):
        if model == InternshipAdvertisement:
            m = InternshipOffer
        else:
            m = JobOffer
        return model.objects.filter(
            id__in=m.objects.filter(student__user=user).values_list('profile'))

    def get_offers(self, profile, model):
        if not profile.banned:
            if profile.program_branch.check_gpa:
                if profile.gender == 'Male':
                    offers = model.objects.filter(min_gpa__lte=profile.gpa, min_ug_gpa__lte=profile.ug_gpa,
                                                  eligible_program_branch__getter__contains=profile.program_branch.getter,
                                                  only_female=False, show_company=True).difference(self.get_applied_ad_list(profile.user, model))
                else:
                    offers = model.objects.filter(min_gpa__lte=profile.gpa, min_ug_gpa__lte=profile.ug_gpa,
                                                  eligible_program_branch__getter__contains=profile.program_branch.getter,
                                                  show_company=True).difference(self.get_applied_ad_list(profile.user, model))
            else:
                if profile.gender == 'Male':
                    offers = model.objects.filter(min_gpa__lte=profile.gpa,
                                                  eligible_program_branch__getter__contains=profile.program_branch.getter,
                                                  only_female=False, show_company=True).difference(self.get_applied_ad_list(profile.user, model))
                else:
                    offers = model.objects.filter(min_gpa__lte=profile.gpa,
                                                  eligible_program_branch__getter__contains=profile.program_branch.getter,
                                                  show_company=True).difference(self.get_applied_ad_list(profile.user, model))

            return offers

    def get(self, request):
        show = get_config_value('ShowAdertisements')
        profile = get_object_or_404(StudentProfile, user=request.user)
        IntershipYears = get_config_value('IntershipYears')
        JobYears = get_config_value('JobYears')
        if profile.banned:
            Response({'Error': 'You are Banned', }, status.HTTP_403_FORBIDDEN)
        if profile.placed:
            Response({'Error': 'You are Placed', }, status.HTTP_403_FORBIDDEN)
        year_combo = profile.program_branch.getter.split('/')[0] + str(profile.year)
        offers = {}
        if year_combo in IntershipYears:
            model = InternshipAdvertisement
            serializer = InternshipAdvertisementSerializer
            off = self.get_offers(profile, model)
            offers['Internships'] = serializer(off, many=True).data if show else []
        if year_combo in JobYears:
            model = JobAdvertisement
            serializer = JobAdvertisementSerializer
            off = self.get_offers(profile, model)
            offers['Jobs'] = serializer(off, many=True).data if show else []
        return Response(offers, status.HTTP_200_OK)


class AppliedOffers(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        data = {}
        off = InternshipOffer.objects.filter(student__user=request.user)
        data['Internships'] = InternshipOfferSerializer(off, many=True).data
        off = JobOffer.objects.filter(student__user=request.user)
        data['Jobs'] = JobOfferSerializer(off, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request,):
        data = {}
        for key in request.data.keys():
            data[key] = request.data.get(key)
        user = request.user
        if data['type'] == 'Intern':
            model = InternshipOffer
            model_ad = InternshipAdvertisement
        elif data['type'] == 'Job':
            model = JobOffer
            model_ad = JobAdvertisement
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ad_id = data.pop('ad_id')
        ad = get_object_or_404(model_ad, id=ad_id)
        student = get_object_or_404(StudentProfile, user=user)
        if not ad.allow_without_resume:
            rs_id = data.pop('resume')
            res = get_object_or_404(Resume, id=rs_id)
            model.objects.create(profile=ad, resume=res, student=student, company=ad.company)
        else:
            model.objects.create(profile=ad, student=student, company=ad.company)
        return Response(status=status.HTTP_200_OK)


class SendSuggestionsAndInquiry(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request,):
        data = {}
        for key in request.data.keys():
            data[key] = request.data.get(key)
        user = request.user
        profile = get_object_or_404(StudentProfile, user=user)
        name = profile
        roll_no = user.username
        email = user.email
        branch = profile.program_branch.name
        send_mail_to = data['sendto']
        feedback_subject = data['subject']
        feedback_text = data['text']
        feedback_category = data['category']
        from_email = settings.SERVER_EMAIL
        CCList = [i.email for i in OfficeMails.objects.filter(category="CC")]
        BCCList = [i.email for i in OfficeMails.objects.filter(category="BCC")]
        # Send mail
        with get_connection(
                username=from_email,
                password=settings.SERVER_EMAIL_PASSWORD
        ) as connection:
            subject = feedback_subject
            to_email = [send_mail_to, ]
            cc = CCList
            bcc = BCCList
            html_content = render_to_string("student/feedback_email_template.html",
                                            {'name': name, 'branch': branch,
                                             'roll_no': roll_no, 'email': email, 'feedback_type': feedback_category,
                                             'feedback_text': feedback_text})
            text_content = strip_tags(html_content)
            message = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=to_email,
                                             cc=cc, bcc=bcc, connection=connection)
            message.attach_alternative(html_content, "text/html")
            message.send()

        # Confirmation mail to user
        from_success_email = settings.SERVER_EMAIL
        with get_connection(
                username=from_success_email,
                password=settings.SERVER_EMAIL_PASSWORD
        ) as connection:
            subject = feedback_category + ' ' + 'received'
            to_email = [email, ]
            html_content = render_to_string("student/feedback_confirmation.html",
                                            {'feedback_type': feedback_category})
            text_content = strip_tags(html_content)
            message = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_success_email, to=to_email,
                                             connection=connection)
            message.attach_alternative(html_content, "text/html")
            message.send()

        return Response(status=status.HTTP_200_OK)


class Advertisement(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, id):
        internship = InternshipAdvertisement.objects.filter(id=id)
        if internship.exists():
            data = InternshipAdvertisementSerializer(internship[0]).data
            data['type'] = 'Internship'
            return Response(data, status=status.HTTP_200_OK)
        job = JobAdvertisement.objects.filter(id=id)
        if job.exists():
            data = JobAdvertisementSerializer(job[0]).data
            data['type'] = 'Job'
            return Response(data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class GetProgramAndBranch(APIView):
    def get(self, request):
        data = ProgramAndBranch.objects.all()
        serializer = ProgramAndBranchSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
