#ifndef JSONPROTOCOL_HPP
#define JSONPROTOCOL_HPP

#include <QJsonDocument>
#include <QJsonObject>
#include <QTcpSocket>

class JsonProtocol {
public:
    JsonProtocol() {
        sock = nullptr;
        server_version = "";
        counter = -1;
    };
    JsonProtocol(QTcpSocket* socket, QString server_version);
    ~JsonProtocol();

    int     get_header_size();
    QString get_proto_version();
    QString get_server_version();

    void        send_message(QString operation, QJsonObject parameters);
    QJsonObject receive_message();

private:
    QByteArray _receive_exact(int num_bytes, int max_chunk_size = 2048);

    static const int     header_size;
    static const QString proto_version;
    QTcpSocket*          sock;
    QString              server_version;
    qint32               counter;
};

#endif // JSONPROTOCOL_HPP
