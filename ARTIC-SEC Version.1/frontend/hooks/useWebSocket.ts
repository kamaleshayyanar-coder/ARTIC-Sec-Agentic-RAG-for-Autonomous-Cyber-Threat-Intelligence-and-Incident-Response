"use client";

import { useEffect, useState, useCallback } from "react";
import { defaultWebSocketClient } from "@/lib/websocket";

export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    defaultWebSocketClient.connect();

    const unsubStatus = defaultWebSocketClient.onStatus((status) => {
      setConnected(status);
    });

    const unsubMsg = defaultWebSocketClient.onMessage((msg) => {
      setLastMessage(msg);
    });

    return () => {
      unsubStatus();
      unsubMsg();
    };
  }, []);

  const sendMessage = useCallback((data: any) => {
    defaultWebSocketClient.send(data);
  }, []);

  return { connected, lastMessage, sendMessage };
}
