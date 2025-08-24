import { ApplicationConfig } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { MessageFormComponent } from './message-form/message-form.component';

// The root component for the app
export const App = MessageFormComponent;

// The app config
export const appConfig: ApplicationConfig = {
  providers: [provideHttpClient()]
};
