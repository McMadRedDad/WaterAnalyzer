#ifndef MAINWINDOW_HPP
#define MAINWINDOW_HPP

#include <QMainWindow>
#include <QMessageBox>
#include <QProcess>
#include <QTcpSocket>
#include <QTimer>
#include "clickableqwidget.hpp"
#include "jsonprotocol.hpp"

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

struct STATE {
    enum CurrPage { BAD = -1, IMPORT, SELECTION, RESULT } page;
    QList<ClickableQWidget *> pages; // same order as CurrPage
};

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void on_pushButton_back_clicked();
    void on_pushButton_showLog_clicked();

private:
    STATE state;

    QProcess    *backend;
    QTcpSocket  *json_sock;
    QTcpSocket  *http_sock;
    QHostAddress backend_host;
    quint16      json_port;
    quint16      http_port;
    JsonProtocol proto;

    Ui::MainWindow *ui;
    QTimer          timer_status;

    void prepare_backend();
    void backend_stdout();
    void init_connections();
    void _connect_socket(QAbstractSocket *socket, QHostAddress address, quint16 port);
    void socket_error();
    void socket_read();

    void set_status_message(bool good, QString message, short msec);
    void clear_status();
    void append_log(QString type, QString line);

    void closeEvent(QCloseEvent *e) override;
    void import_clicked();
};
#endif // MAINWINDOW_HPP
