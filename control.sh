#!/bin/bash

cd /root/ai-analysts
source venv/bin/activate

case "$1" in
    start)
        echo "🚀 Starting AI Analyst system..."
        docker start weaviate 2>/dev/null
        sleep 5
        # Kill any existing chat servers
        pkill -f google_chat_server.py 2>/dev/null
        sleep 2
        # Start chat server
        python google_chat_server.py > chat_server.log 2>&1 &
        sleep 3
        echo "✅ System started"
        ;;
    stop)
        echo "🛑 Stopping AI Analyst system..."
        pkill -f google_chat_server.py
        docker stop weaviate 2>/dev/null
        echo "✅ System stopped"
        ;;
    status)
        echo "📊 System Status:"
        echo -n "Weaviate: "
        docker ps 2>/dev/null | grep weaviate > /dev/null && echo "✅ Running" || echo "❌ Stopped"
        echo -n "Chat Server: "
        curl -s http://localhost:8000/health > /dev/null && echo "✅ Running" || echo "❌ Stopped"
        echo "📍 Public IP: $(curl -s http://checkip.amazonaws.com 2>/dev/null)"
        ;;
    restart)
        $0 stop
        sleep 3
        $0 start
        ;;
    test)
        echo "🧪 Running test analysis..."
        python main.py "Test: Analyze the electric vehicle charging market"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|test}"
        exit 1
        ;;
esac
