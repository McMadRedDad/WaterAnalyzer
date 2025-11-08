#include "resulttab.hpp"
#include "ui_resulttab.h"

ResultTab::ResultTab(QWidget *parent) : QWidget(parent), ui(new Ui::ResultTab) {
    ui->setupUi(this);
    ui->tb_stats->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    ui->tb_stats->verticalHeader()->setSectionResizeMode(QHeaderView::Stretch);
}

ResultTab::~ResultTab() {
    delete ui;
}

void ResultTab::set_preview(QPixmap image) {
    ui->lbl_preview->clear();
    ui->lbl_preview->setPixmap(image);
}

uint ResultTab::get_preview_width() {
    return ui->lbl_preview->width() - 2;
}

uint ResultTab::get_preview_height() {
    return ui->lbl_preview->height() - 2;
}

void ResultTab::set_caption(QString caption) {
    ui->lbl_caption->setText(caption);
}

void ResultTab::set_statistics(double min, double max, double mean, double stdev, QString ph_unit) {
    QStringList stats = {QString::number(min), QString::number(max), QString::number(mean), QString::number(stdev), ph_unit};
    for (int i = 0; i < ui->tb_stats->rowCount() && i < stats.length(); i++) {
        QTableWidgetItem *prev = ui->tb_stats->takeItem(i, 1);
        delete prev;
        QTableWidgetItem *it = new QTableWidgetItem(stats[i]);
        ui->tb_stats->setItem(i, 1, it);
    }
}

void ResultTab::set_description(QString text) {
    ui->lbl_description->setText(text);
}

void ResultTab::hide_stats() {
    ui->tb_stats->hide();
    ui->widget_text->layout()->removeWidget(ui->tb_stats);
}

void ResultTab::on_pb_refresh_clicked() {
    emit refresh_preview();
}

void ResultTab::on_pb_export_index_clicked() {
    emit export_index();
}

void ResultTab::on_pb_export_text_clicked() {
    QString description;
    // text from table + text from label
    emit export_text(description);
}
