import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { MessageService } from './message.service';

describe('MessageService', () => {
  let service: MessageService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        MessageService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(MessageService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should send a message successfully', () => {
    const mockResponse = 'Message sent successfully';
    const formData = new FormData();
    formData.append('name', 'John');
    formData.append('email', 'john@test.com');
    formData.append('content', 'Hello!');

    service.sendMessage(formData).subscribe(response => {
      expect(response).toBe(mockResponse);
    });

    const req = httpMock.expectOne('http://localhost:8080/api/messages');
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBeTrue();
    req.flush(mockResponse);
  });

  it('should handle error response', () => {
    const formData = new FormData();
    formData.append('name', 'Jane');
    formData.append('email', 'jane@test.com');
    formData.append('content', 'Hi!');

    service.sendMessage(formData).subscribe({
      next: () => fail('Expected error, but got success'),
      error: (err) => {
        expect(err.status).toBe(500);
        expect(err.statusText).toBe('Server Error');
      }
    });

    const req = httpMock.expectOne('http://localhost:8080/api/messages');
    req.flush('Error occurred', { status: 500, statusText: 'Server Error' });
  });
});