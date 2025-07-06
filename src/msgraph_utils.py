#!/usr/bin/env python3
import asyncio
from azure.identity.aio import ClientSecretCredential
import base64
from config import Config
import json
from msgraph import GraphServiceClient
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import SendMailPostRequestBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.attachment import Attachment
from msgraph.generated.models.file_attachment import FileAttachment

tenant_id = Config.MSGRAPH_TENANT_ID
client_id = Config.MSGRAPH_CLIENT_ID
client_secret = Config.MSGRAPH_CLIENT_SECRET

email_subject = 'TEST Data Request Submission Confirmation - GUTS Consortium'
email_sender = 'gutsdata@eur.nl'
email_reply_to = 'gutsdata@eur.nl'
email_body = """
Dear {name}

Thank you for submitting your data request to the GUTS Consortium. Your request has been received and will now be evaluated by the GUTS Steering Committee.

Attached you will find a receipt summarizing the details of your request for your reference.

Please note that the evaluation process should take no longer than three weeks on average. You will receive a notification once a decision has been made.

If you have any questions in the meantime, feel free to contact the data management team at gutsdata@eur.nl.

Best regards,
The GUTS Data Management Team
"""


def create_graph_client():
    """
    """
    # The client credentials flow requires that you request the
    # /.default scope, and pre-configure your permissions on the
    # app registration in Azure. An administrator must grant consent
    # to those permissions beforehand.
    scopes = ['https://graph.microsoft.com/.default']

    # azure.identity.aio
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret)

    return GraphServiceClient(credential, scopes), credential



async def send_mail(graph_client, body, to_email, data = {'name': 'Jon Doe'}):
    """
    """
    json_string = json.dumps(data, indent=4)
    json_bytes = json_string.encode('utf-8')
    request_body = SendMailPostRequestBody(
        message = Message(
            subject = email_subject,
            body = ItemBody(
                content_type = BodyType.Text,
                content = body,
            ),
            to_recipients = [
                Recipient(
                    email_address = EmailAddress(
                        address = to_email,
                    ),
                ),
            ],
            reply_to=[
                Recipient(
                    email_address = EmailAddress(
                        address = email_reply_to,
                    ),
                ),
            ],
            attachments = [
                FileAttachment(
                    odata_type = "#microsoft.graph.fileAttachment",
                    name = "guts_data_request.json",
                    content_type = "application/json",
                    content_bytes = json_bytes,
                ),
            ],
        ),
    )

    await graph_client.users.by_user_id(email_sender).send_mail.post(request_body)


async def test():
    """
    """
    graph_client, credential = create_graph_client()
    response = await send_mail(graph_client, email_body.format(name='Jon Doe'), "heunis@essb.eur.nl")
    print(response)
    await credential.close()


if __name__ == '__main__':
    asyncio.run(test())