from langchain_core.tools import tool
from typing import Optional, List, Dict, Any, Union
from auth import authenticate_google

service = authenticate_google()

@tool
def fetch_top_email() -> Dict[str, Any]:
    """
    Fetches the latest email from the user's Gmail inbox.
    
    Args:
        None
        
    Returns:
        dict: A dictionary containing the email data with keys like 'id', 'subject', 'from', 'date', and 'body'.
    """
    try:
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return {"status": "error", "message": "No emails found"}
        
        msg_id = messages[0]['id']
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        
        # Process the message to extract needed information
        headers = message['payload']['headers']
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown')
        date = next((header['value'] for header in headers if header['name'].lower() == 'date'), 'Unknown')
        
        # Get email body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = part.get('body', {}).get('data', '')
                    import base64
                    if body:
                        body = base64.urlsafe_b64decode(body).decode('utf-8')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            import base64
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        return {
            "id": msg_id,
            "subject": subject,
            "from": sender,
            "date": date,
            "body": body,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@tool
def fetch_specific_email(query: str) -> Dict[str, Any]:
    """
    Fetches the first email matching a given Gmail search query.
    
    Args:
        query: A Gmail search query string (e.g., "from:amazon.com" or "subject:Invoice")
        Compose the query on your own.
        
    Returns:
        dict: A dictionary containing the email data with keys like 'id', 'subject', 'from', 'date', and 'body'.
    """
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return {"status": "error", "message": f"No emails found matching query: {query}"}
        
        msg_id = messages[0]['id']
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        
        # Process the message to extract needed information
        headers = message['payload']['headers']
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown')
        date = next((header['value'] for header in headers if header['name'].lower() == 'date'), 'Unknown')
        
        # Get email body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = part.get('body', {}).get('data', '')
                    import base64
                    if body:
                        body = base64.urlsafe_b64decode(body).decode('utf-8')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            import base64
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        return {
            "id": msg_id,
            "subject": subject,
            "from": sender,
            "date": date,
            "body": body,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@tool
def reply_to_email(email_id: str, reply_text: str) -> Dict[str, Any]:
    """
    Sends a reply to a specific email.
    
    Args:
        email_id: The ID of the email to reply to.
        reply_text: The text content of the reply.
        
    Returns:
        dict: A status dictionary indicating success or failure.
    """
    try:
        # First, get the email we're replying to
        message = service.users().messages().get(userId='me', id=email_id, format='metadata').execute()
        
        # Extract thread ID and email headers
        thread_id = message['threadId']
        headers = message['payload']['headers']
        
        # Get necessary header information
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
        if not subject.startswith('Re:'):
            subject = f"Re: {subject}"
            
        to_address = next((header['value'] for header in headers if header['name'].lower() == 'from'), None)
        if not to_address:
            return {"status": "error", "message": "Could not determine recipient address"}
        
        # Get references and in-reply-to headers if they exist
        references = next((header['value'] for header in headers if header['name'].lower() == 'message-id'), None)
        
        # Create email message
        import base64
        from email.mime.text import MIMEText
        
        message = MIMEText(reply_text)
        message['to'] = to_address
        message['subject'] = subject
        
        if references:
            message['References'] = references
            message['In-Reply-To'] = references
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send the message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message, 'threadId': thread_id}
        ).execute()
        
        return {
            "status": "success", 
            "message": "Reply sent successfully", 
            "message_id": sent_message['id']
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@tool
def list_emails(max_results: int = 5, query: str = "") -> List[Dict[str, Any]]:
    """
    Lists emails from the user's inbox with optional filters.
    
    Args:
        max_results: Maximum number of emails to retrieve (default: 5).
        query: A Gmail search query string (e.g., "label:UNREAD from:example@gmail.com").
        Compose the query on your own.
        
    Returns:
        list: A list of dictionaries, each containing email metadata.
    """
    try:
        results = service.users().messages().list(
            userId='me', 
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return []
            
        email_list = []
        
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
            sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown')
            date = next((header['value'] for header in headers if header['name'].lower() == 'date'), 'Unknown')
            
            # Get labels
            labels = msg.get('labelIds', [])
            
            email_list.append({
                "id": message['id'],
                "thread_id": msg['threadId'],
                "subject": subject,
                "from": sender,
                "date": date,
                "labels": labels,
                "snippet": msg.get('snippet', '')
            })
        
        return email_list
    except Exception as e:
        return [{"status": "error", "message": str(e)}]
    
@tool
def get_email_id(query: str) -> Dict[str, Any]:
    """
    Retrieves the ID of an email matching the given search query.
    Always use this tool to get the id if user doesn't provides one.
    
    Args:
        query: A Gmail search query string (e.g., "from:amazon.com" or "subject:Invoice" or "from: Haaris Sharma").
        
    Returns:
        dict: A dictionary containing the email ID and basic information, or error status.
    """
    try:
        # Search for emails matching the query
        results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return {"status": "error", "message": f"No emails found matching query: {query}"}
        
        # Get the ID of the first matching email
        msg_id = messages[0]['id']
        
        # Fetch basic metadata about the email
        message = service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
        
        # Extract header information
        headers = message['payload']['headers']
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown')
        date = next((header['value'] for header in headers if header['name'].lower() == 'date'), 'Unknown')
        
        return {
            "status": "success",
            "id": msg_id,
            "thread_id": message.get('threadId', ''),
            "from": sender,
            "date": date,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@tool
def send_email(
    to: str, 
    subject: str, 
    body: str, 
    cc: Optional[Union[str, List[str]]] = None, 
    bcc: Optional[Union[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Sends a new email to specified recipients.
    
    Args:
        to: Email address(es) of the primary recipient(s). Can be a string for a single recipient 
            or a comma-separated string for multiple recipients.
        subject: Subject line of the email.
        body: The main content/body of the email.
        cc: Optional. Email address(es) to carbon copy. Can be a string or list of strings.
        bcc: Optional. Email address(es) to blind carbon copy. Can be a string or list of strings.
        
    Returns:
        dict: A status dictionary containing success/error information and the message ID if successful.
    """
    try:
        # Import required libraries
        import base64
        from email.mime.text import MIMEText
        
        # Create the message
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        # Add CC recipients if provided
        if cc:
            if isinstance(cc, list):
                cc = ", ".join(cc)
            message['cc'] = cc
            
        # Add BCC recipients if provided
        if bcc:
            if isinstance(bcc, list):
                bcc = ", ".join(bcc)
            message['bcc'] = bcc
        
        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Create the email payload
        create_message = {
            'raw': encoded_message
        }
        
        # Send the message
        sent_message = service.users().messages().send(
            userId='me', 
            body=create_message
        ).execute()
        
        return {
            "status": "success",
            "message": "Email sent successfully",
            "message_id": sent_message['id']
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }