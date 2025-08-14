# for test purpose only
# # myapp/views.py
# import requests
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
#
# from django.conf import settings
# from rest_framework.permissions import AllowAny
# from core_apps.odk.serializers import FormUploadSerializer
#
#
# class FormUploadView(APIView):
#     permission_classes = [AllowAny]
#     def post(self, request):
#         serializer = FormUploadSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#         project_id = serializer.validated_data['project_id']
#         form_file = serializer.validated_data['form_file']
#         ignore_warnings = serializer.validated_data['ignore_warnings']
#         publish = serializer.validated_data['publish']
#         form_id_fallback = serializer.validated_data.get('form_id_fallback', '')
#
#         # Determine Content-Type based on file extension
#         content_type = (
#             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#             if form_file.name.endswith('.xlsx') else
#             'application/vnd.ms-excel'
#             if form_file.name.endswith('.xls') else
#             'application/xml'
#         )
#
#         # Prepare headers
#         headers = {
#             'Authorization': f'Bearer {settings.ODK_API_TOKEN}',
#             'Content-Type': content_type,
#
#         }
#         if form_id_fallback and content_type != 'application/xml':
#             headers['X-XlsForm-FormId-Fallback'] = form_id_fallback
#
#         # Prepare query parameters
#         params = {
#             'ignoreWarnings': str(ignore_warnings).lower(),
#             'publish': str(publish).lower(),
#         }
#
#         # ODK Central API URL
#         url = f'{settings.ODK_CENTRAL_URL}/projects/{project_id}/forms'
#
#         try:
#             # Send the file to ODK Central
#             response = requests.post(
#                 url,
#                 headers=headers,
#                 params=params,
#                 files={'file': (form_file.name, form_file, content_type)},
#                 verify=False
#             )
#
#             # Handle response
#             if response.status_code == 200:
#                 return Response(response.json(), status=status.HTTP_200_OK)
#             elif response.status_code == 400:
#                 return Response(response.json(), status=status.HTTP_400_BAD_REQUEST)
#             elif response.status_code == 403:
#                 return Response(
#                     {"message": "Unauthorized access to ODK Central"},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
#             elif response.status_code == 409:
#                 return Response(
#                     {"message": "Form with this ID already exists"},
#                     status=status.HTTP_409_CONFLICT
#                 )
#             else:
#                 return Response(
#                     {"message": "Unexpected error from ODK Central", "details": response.text},
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
#
#         except requests.RequestException as e:
#             return Response(
#                 {"message": "Failed to connect to ODK Central", "error": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
