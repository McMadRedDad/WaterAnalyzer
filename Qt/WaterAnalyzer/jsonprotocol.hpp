#ifndef JSONPROTOCOL_H
#define JSONPROTOCOL_H

#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>

class JsonProtocol {
public:
    JsonProtocol() {
        server_version = "";
        counter = -1;
    };
    JsonProtocol(QString server_version);

    QJsonObject ping();
    QJsonObject shutdown();
    QJsonObject import_gtiff(QString file);
    QJsonObject calc_preview(int r, int g, int b, uint width, uint height);
    QJsonObject calc_index(QString index, QList<int> ids);
    QJsonObject set_satellite(QString satellite);

    void    inc_counter();
    QString get_proto_version();
    QString get_server_version();
    quint32 get_counter();

private:
    QJsonObject construct_json(QString operation, QJsonObject parameters);

    static const QString proto_version;
    QString              server_version;
    qint32               counter;
};

#endif // JSONPROTOCOL_H
