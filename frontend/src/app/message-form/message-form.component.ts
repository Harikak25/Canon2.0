import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { MessageService } from '../message.service';

@Component({
  selector: 'app-message-form',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './message-form.component.html',
  styleUrls: ['./message-form.component.css']
})
export class MessageFormComponent implements OnInit {
  firstName = '';
  lastName = '';
  email = '';
  subject = '';
  message = '';
  file: File | null = null;

  statusMsg = '';
  statusMsgColor: 'success' | 'error' | '' = '';

  constructor(private messageService: MessageService) {}

  ngOnInit() {
    // Test message on init to check UI binding
    this.statusMsg = 'Ready to send your message!';
    this.statusMsgColor = 'success';
  }

  onFileSelected(event: any) {
    this.file = event.target.files[0] || null;
  }

  async sendMessage() {
    this.statusMsg = '';
    this.statusMsgColor = '';

    if (!this.firstName || !this.lastName || !this.email || !this.subject || !this.message) {
      this.statusMsg = 'Please fill out all fields!';
      this.statusMsgColor = 'error';
      return;
    }

    let attachment_name = null;
    let attachment_bytes = null;

    if (this.file) {
      attachment_name = this.file.name;
      const arrayBuffer = await this.file.arrayBuffer();
      const bytes = new Uint8Array(arrayBuffer);
      let binary = '';
      for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      attachment_bytes = btoa(binary);
    }

    const jsonPayload = {
      first_name: this.firstName,
      last_name: this.lastName,
      email_id: this.email,
      subject: this.subject,
      body: this.message,
      attachment_name: attachment_name,
      attachment_bytes: attachment_bytes
    };

    this.messageService.sendMessage(jsonPayload).subscribe({
      next: () => {
        console.log('Success callback triggered');
        this.statusMsg = 'Message sent successfully!';
        this.statusMsgColor = 'success';

        // Reset form fields
        this.firstName = '';
        this.lastName = '';
        this.email = '';
        this.subject = '';
        this.message = '';
        this.file = null;

        // Reset file input visually
        const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      },
      error: (err) => {
        console.error('Error sending message:', err);
        this.statusMsg = 'Failed to send message.';
        this.statusMsgColor = 'error';
      }
    });
  }
}
