import React, { useEffect, useState, useRef } from 'react';
import api from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import {
  MessageSquare,
  Send,
  Image as ImageIcon,
  Video,
  FileText,
  Sparkles,
  Phone,
  Search,
  Filter,
  Check,
  CheckCheck,
} from 'lucide-react';
import { format } from 'date-fns';

export const WhatsAppCRM = () => {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [aiSuggestion, setAiSuggestion] = useState('');
  const [loadingAI, setLoadingAI] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchConversations();
    fetchTemplates();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.customer_phone);
    }
  }, [selectedConversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = async () => {
    try {
      const response = await api.get('/whatsapp/conversations');
      setConversations(response.data);
    } catch (error) {
      toast.error('Failed to fetch conversations');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (phone) => {
    try {
      const response = await api.get(`/whatsapp/messages/history/${phone}`);
      setMessages(response.data);
    } catch (error) {
      toast.error('Failed to fetch messages');
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/whatsapp/templates');
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates');
    }
  };

  const sendMessage = async () => {
    if (!messageText.trim() || !selectedConversation) return;

    setSending(true);
    try {
      await api.post('/whatsapp/messages/send', null, {
        params: {
          to: selectedConversation.customer_phone,
          message: messageText,
          order_id: selectedConversation.order_id,
        },
      });

      setMessages([...messages, {
        id: Date.now().toString(),
        content: messageText,
        is_incoming: false,
        created_at: new Date().toISOString(),
        status: 'sent',
      }]);

      setMessageText('');
      toast.success('Message sent');
    } catch (error) {
      toast.error('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const getAISuggestion = async (messageType = 'general') => {
    if (!selectedConversation) return;

    setLoadingAI(true);
    try {
      const response = await api.post(
        '/whatsapp/ai/suggest-message',
        null,
        {
          params: {
            context: messageText || 'Generate a message',
            message_type: messageType,
            order_id: selectedConversation.order_id,
            phone: selectedConversation.customer_phone,
          },
        }
      );

      setAiSuggestion(response.data.suggestion);
      toast.success('AI suggestion generated');
    } catch (error) {
      toast.error('Failed to get AI suggestion');
    } finally {
      setLoadingAI(false);
    }
  };

  const useAISuggestion = () => {
    setMessageText(aiSuggestion);
    setAiSuggestion('');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'sent':
        return <Check className="w-3 h-3 text-muted-foreground" />;
      case 'delivered':
        return <CheckCheck className="w-3 h-3 text-muted-foreground" />;
      case 'read':
        return <CheckCheck className="w-3 h-3 text-primary" />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)]" data-testid="whatsapp-crm">
      <div className="mb-4">
        <h1 className="text-3xl font-bold font-[Manrope] text-foreground tracking-tight">
          WhatsApp CRM
        </h1>
        <p className="text-muted-foreground mt-1">
          Manage customer conversations with AI-powered assistance
        </p>
      </div>

      <div className="grid grid-cols-12 gap-4 h-[calc(100%-5rem)]">
        {/* Conversations List */}
        <Card className="col-span-12 lg:col-span-4 border-border/60 flex flex-col" data-testid="conversations-panel">
          <CardHeader className="pb-3">
            <CardTitle className="font-[Manrope] text-lg">Conversations</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-0">
            {conversations.length === 0 ? (
              <div className="p-4 text-center text-muted-foreground">
                <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No conversations yet</p>
              </div>
            ) : (
              <div className="space-y-1">
                {conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => setSelectedConversation(conv)}
                    className={`w-full p-4 text-left border-b border-border/40 hover:bg-secondary/30 transition-colors ${
                      selectedConversation?.id === conv.id ? 'bg-secondary/50' : ''
                    }`}
                    data-testid={`conversation-${conv.id}`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <p className="font-medium text-sm">{conv.customer_name}</p>
                      <span className="text-xs text-muted-foreground">
                        {conv.last_message_time && format(new Date(conv.last_message_time), 'HH:mm')}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">{conv.last_message || 'No messages'}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {conv.message_count} msgs
                      </Badge>
                      {conv.status === 'active' && (
                        <Badge className="bg-primary/20 text-primary text-xs">Active</Badge>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Chat Area */}
        <Card className="col-span-12 lg:col-span-8 border-border/60 flex flex-col" data-testid="chat-panel">
          {selectedConversation ? (
            <>
              <CardHeader className="pb-3 border-b border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="font-[Manrope] text-lg">
                      {selectedConversation.customer_name}
                    </CardTitle>
                    <p className="text-sm text-muted-foreground font-[JetBrains_Mono]">
                      {selectedConversation.customer_phone}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" data-testid="call-customer-button">
                    <Phone className="w-4 h-4 mr-2" />
                    Call
                  </Button>
                </div>
              </CardHeader>

              <CardContent className="flex-1 overflow-y-auto p-4 space-y-3" data-testid="messages-container">
                {messages.map((msg, idx) => (
                  <div
                    key={msg.id || idx}
                    className={`flex ${msg.is_incoming ? 'justify-start' : 'justify-end'}`}
                    data-testid={`message-${idx}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-lg p-3 ${
                        msg.is_incoming
                          ? 'bg-secondary text-foreground'
                          : 'bg-primary text-primary-foreground'
                      }`}
                    >
                      {msg.media_url && (
                        <div className="mb-2">
                          {msg.message_type === 'image' ? (
                            <img src={msg.media_url} alt="" className="rounded max-w-full" />
                          ) : msg.message_type === 'video' ? (
                            <video src={msg.media_url} controls className="rounded max-w-full" />
                          ) : (
                            <a href={msg.media_url} className="text-sm underline" target="_blank" rel="noopener noreferrer">
                              View attachment
                            </a>
                          )}
                        </div>
                      )}
                      <p className="text-sm">{msg.content}</p>
                      <div className="flex items-center justify-end gap-1 mt-1">
                        <span className="text-xs opacity-70">
                          {format(new Date(msg.created_at), 'HH:mm')}
                        </span>
                        {!msg.is_incoming && getStatusIcon(msg.status)}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </CardContent>

              {/* AI Suggestion */}
              {aiSuggestion && (
                <div className="px-4 py-2 bg-primary/5 border-t border-border">
                  <div className="flex items-start gap-2">
                    <Sparkles className="w-4 h-4 text-primary mt-1" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-primary mb-1">AI Suggestion:</p>
                      <p className="text-sm text-foreground">{aiSuggestion}</p>
                    </div>
                    <Button size="sm" variant="outline" onClick={useAISuggestion} data-testid="use-ai-suggestion">
                      Use
                    </Button>
                  </div>
                </div>
              )}

              {/* Message Input */}
              <div className="p-4 border-t border-border">
                <div className="flex gap-2 mb-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => getAISuggestion('delivery_confirmation')}
                    disabled={loadingAI}
                    data-testid="ai-suggest-delivery"
                  >
                    <Sparkles className="w-4 h-4 mr-1" />
                    Delivery
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => getAISuggestion('installation_inquiry')}
                    disabled={loadingAI}
                    data-testid="ai-suggest-installation"
                  >
                    <Sparkles className="w-4 h-4 mr-1" />
                    Installation
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => getAISuggestion('follow_up')}
                    disabled={loadingAI}
                    data-testid="ai-suggest-followup"
                  >
                    <Sparkles className="w-4 h-4 mr-1" />
                    Follow-up
                  </Button>
                </div>
                <div className="flex gap-2">
                  <Textarea
                    data-testid="message-input"
                    placeholder="Type a message..."
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                      }
                    }}
                    rows={2}
                    className="resize-none"
                  />
                  <div className="flex flex-col gap-2">
                    <Button
                      onClick={sendMessage}
                      disabled={sending || !messageText.trim()}
                      data-testid="send-message-button"
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Select a conversation to start messaging</p>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
