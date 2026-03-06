import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../components/ChatInput';

describe('ChatInput', () => {
  const mockOnSend = jest.fn();

  beforeEach(() => jest.clearAllMocks());

  it('텍스트 입력 + 전송 버튼 렌더링', () => {
    render(<ChatInput onSend={mockOnSend} isStreaming={false} />);

    expect(screen.getByPlaceholderText('메시지를 입력하세요...')).toBeDefined();
    expect(screen.getByRole('button')).toBeDefined();
  });

  it('텍스트 입력 후 버튼 클릭으로 전송', () => {
    render(<ChatInput onSend={mockOnSend} isStreaming={false} />);

    const textarea = screen.getByPlaceholderText('메시지를 입력하세요...');
    fireEvent.change(textarea, { target: { value: '안녕하세요' } });
    fireEvent.click(screen.getByRole('button'));

    expect(mockOnSend).toHaveBeenCalledWith('안녕하세요');
  });

  it('Enter 키로 전송 (Shift+Enter는 줄바꿈)', () => {
    render(<ChatInput onSend={mockOnSend} isStreaming={false} />);

    const textarea = screen.getByPlaceholderText('메시지를 입력하세요...');
    fireEvent.change(textarea, { target: { value: '질문입니다' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });

    expect(mockOnSend).toHaveBeenCalledWith('질문입니다');
  });

  it('빈 입력이면 전송 불가 (버튼 disabled)', () => {
    render(<ChatInput onSend={mockOnSend} isStreaming={false} />);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();

    fireEvent.click(button);
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('스트리밍 중이면 textarea disabled + 버튼 disabled', () => {
    render(<ChatInput onSend={mockOnSend} isStreaming={true} />);

    const textarea = screen.getByPlaceholderText('메시지를 입력하세요...');
    expect(textarea).toBeDisabled();
  });

  it('2000자 초과 입력 방지', () => {
    render(<ChatInput onSend={mockOnSend} isStreaming={false} />);

    const textarea = screen.getByPlaceholderText('메시지를 입력하세요...');
    const longText = 'a'.repeat(2100);
    fireEvent.change(textarea, { target: { value: longText } });

    expect((textarea as HTMLTextAreaElement).value).toHaveLength(2000);
  });

  it('2000자 근처에서 남은 글자 수 표시', () => {
    render(<ChatInput onSend={mockOnSend} isStreaming={false} />);

    const textarea = screen.getByPlaceholderText('메시지를 입력하세요...');
    fireEvent.change(textarea, { target: { value: 'a'.repeat(1850) } });

    expect(screen.getByText('150자 남음')).toBeDefined();
  });
});
