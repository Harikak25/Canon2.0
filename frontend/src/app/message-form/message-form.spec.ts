import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { MessageFormComponent } from './message-form.component';
import { MessageService } from '../message.service';

describe('MessageFormComponent (spec file)', () => {
  let component: MessageFormComponent;
  let fixture: ComponentFixture<MessageFormComponent>;
  let mockMessageService: jasmine.SpyObj<MessageService>;

  beforeEach(async () => {
    mockMessageService = jasmine.createSpyObj('MessageService', ['sendMessage']);

    await TestBed.configureTestingModule({
      imports: [MessageFormComponent], // standalone component
      providers: [{ provide: MessageService, useValue: mockMessageService }]
    }).compileComponents();

    fixture = TestBed.createComponent(MessageFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default status message', () => {
    expect(component.statusMsg).toBe('Ready to send your message!');
    expect(component.statusMsgColor).toBe('success');
  });

  it('should handle file selection', () => {
    const file = new File(['dummy'], 'test.txt', { type: 'text/plain' });
    const event = { target: { files: [file] } } as unknown as Event;
    component.onFileSelected(event);
    expect(component.file).toBe(file);
  });

  it('should not call service if required fields are missing', () => {
    component.firstName = '';
    component.lastName = '';
    component.email = '';
    component.subject = '';
    component.message = '';

    component.sendMessage();

    expect(component.statusMsg).toBe('Please fill out all fields!');
    expect(component.statusMsgColor).toBe('error');
    expect(mockMessageService.sendMessage).not.toHaveBeenCalled();
  });

  it('should call service and reset form on success', () => {
    component.firstName = 'John';
    component.lastName = 'Doe';
    component.email = 'john@test.com';
    component.subject = 'Hello';
    component.message = 'Test message';

    mockMessageService.sendMessage.and.returnValue(of('Message sent successfully!'));

    component.sendMessage();

    expect(mockMessageService.sendMessage).toHaveBeenCalled();
    expect(component.statusMsg).toBe('Message sent successfully!');
    expect(component.statusMsgColor).toBe('success');
    expect(component.firstName).toBe('');
    expect(component.lastName).toBe('');
    expect(component.email).toBe('');
    expect(component.subject).toBe('');
    expect(component.message).toBe('');
    expect(component.file).toBeNull();
  });

  it('should show error if service call fails', () => {
    component.firstName = 'Jane';
    component.lastName = 'Doe';
    component.email = 'jane@test.com';
    component.subject = 'Hi';
    component.message = 'Test failure';

    mockMessageService.sendMessage.and.returnValue(throwError(() => ({ status: 500 })));

    component.sendMessage();

    expect(mockMessageService.sendMessage).toHaveBeenCalled();
    expect(component.statusMsg).toBe('Failed to send message.');
    expect(component.statusMsgColor).toBe('error');
  });
});