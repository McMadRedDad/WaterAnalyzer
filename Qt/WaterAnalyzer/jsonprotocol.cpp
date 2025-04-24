#include "jsonprotocol.hpp"

const int     JsonProtocol::header_size = 4;
const QString JsonProtocol::proto_version = "1.2.0";

JsonProtocol::JsonProtocol(QTcpSocket *socket, QString server_version) {
    this->sock = socket;
    this->server_version = server_version;
    this->counter = 0;
}

JsonProtocol::~JsonProtocol() {
    if (sock) {
        sock = nullptr; // do not free memory!
    }
}

int JsonProtocol::get_header_size() {
    return header_size;
}

QString JsonProtocol::get_proto_version() {
    return JsonProtocol::proto_version;
}

QString JsonProtocol::get_server_version() {
    return server_version;
}

QByteArray JsonProtocol::_receive_exact(int num_bytes) {
    if (!sock) {
        return QByteArray();
    }

    QByteArray ba;
    while (ba.size() < num_bytes) {
        QByteArray chunk = sock->read(num_bytes - ba.size());
        if (chunk.isEmpty()) {
            return chunk;
        }
        ba.append(chunk);
    }
    return ba;
}

QJsonObject JsonProtocol::receive() {
    if (!sock) {
        return QJsonObject();
    }

    while (sock->bytesAvailable() > 0) {
        QByteArray header_ba = _receive_exact(header_size);
        if (header_ba.isEmpty()) {
            return QJsonObject();
        }
        QDataStream header(header_ba);
        header.setByteOrder(QDataStream::BigEndian);
        quint32 size = 0;
        header >> size;

        QByteArray message_ba = _receive_exact(size);
        if (message_ba.isEmpty()) {
            return QJsonObject();
        }

        return QJsonDocument::fromJson(message_ba).object();
    }

    return QJsonObject();
}

void JsonProtocol::send(QString operation, QJsonObject parameters) {
    if (!sock) {
        return;
    }

    QJsonObject   json{{"proto_version", JsonProtocol::proto_version},
                       {"server_version", this->server_version},
                       {"id", this->counter},
                       {"operation", operation},
                       {"parameters", parameters}};
    QJsonDocument jdoc(json);
    QByteArray    data_ba = jdoc.toJson();

    QByteArray  message;
    QDataStream out(&message, QIODevice::WriteOnly);
    out.setByteOrder(QDataStream::BigEndian);
    out << static_cast<quint32>(data_ba.size());
    message.append(data_ba);

    sock->write(message);
    counter++;
}
