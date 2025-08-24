import { TestBed } from '@angular/core/testing';
import { HttpClient } from '@angular/common/http';
import { App, appConfig } from './app';
import { MessageFormComponent } from './message-form/message-form.component';

describe('App setup', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [...appConfig.providers]
    });
  });

  it('should provide HttpClient from appConfig', () => {
    const http = TestBed.inject(HttpClient);
    expect(http).toBeTruthy();
  });

  it('should set App to MessageFormComponent', () => {
    expect(App).toBe(MessageFormComponent);
  });
});