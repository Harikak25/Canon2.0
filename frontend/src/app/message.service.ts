import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MessageService {

  private apiUrl = 'http://localhost:8000/submit';

  constructor(private http: HttpClient) { }


  // Added to support Angular component calls
  sendMessage(payload: any): Observable<any> {
    return this.http.post<any>(this.apiUrl, payload);
  }
}
