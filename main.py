# import argparse
#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='预约终端start...')
#     identification_parser = parser.add_subparsers('信息认证...')
#
#     identification_parser.add_argument('-u','--username',required=True,help='学号')
#     identification_parser.add_argument('-p','--password',required=True,help='密码')
import argparse
import cmd
import io
import os.path
import sys

import orjson
import stdiomask
import win32api
import win32con

from internal.identity.person import PersonInfo

from internal.info.function import get_construction_info
from internal.util.setting import REFLECT_NAME


class MyCLI(cmd.Cmd):
    person_info: PersonInfo = None
    intro = '欢迎进入图书馆预约程序,可通过help或者?获取帮助.'
    prompt = '>> '
    record: dict = {}
    username, password = '', ''
    key = 'library_reservation_cli'
    priority: list[str] = []
    doc_header= '提供的命令有(通过help command查看帮助):'
    nohelp = '%s 命令不存在!'
    undoc_header = ''

    def do_help(self, arg: str):
        'List available commands with "help" or detailed help with "help cmd".'
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.stdout.write("%s\n" % str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n" % str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]] = 1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd = name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n" % str(self.doc_leader))
            self.print_topics(self.doc_header, cmds_doc, 15, 80)
            self.print_topics(self.misc_header, list(help.keys()), 15, 80)
            self.print_topics(self.undoc_header, cmds_undoc, 15, 80)
            print('预约的正确流程:')
            print('\tcheck -> set_priority -> make')

    def do_quit(self, arg):
        """退出程序并保存已有配置
        """
        if self.person_info is not None:
            with open('.library_config', 'w+') as f:
                storage: dict[str:str] = {'username': self.username, 'password': self.password,
                                          'priority': self.priority}
                for key, val in self.record.items():
                    storage[key] = val
                data = orjson.dumps(storage)
                f.write(data.decode('utf-8'))
            win32api.SetFileAttributes('.library_config', win32con.FILE_ATTRIBUTE_HIDDEN)

        print('Goodbye!')
        return True

    def read_config(self):
        if os.path.exists('.library_config'):
            print('检查到配置项的存在,开始读取配置...')
            with open('.library_config', 'r') as f:
                secret = f.read()
                data = orjson.loads(secret)
                self.username, self.password = data['username'], data['password']
                self.priority = data['priority']
                data.pop('username'), data.pop('password'), data.pop('priority')

                for key, val in data.items():
                    self.record[key] = val
            print('配置读取成功!')
            return True
        print('暂无检查到配置项的存在!')
        return False

    def do_check(self, arg):
        """进行统一身份认证:
    username 学号
    password 密码
        """
        status = self.read_config()
        if not status:
            self.username = input('Enter username:')
            self.password = stdiomask.getpass(prompt='Enter password:')

        print('登录中...')
        try:
            self.person_info = PersonInfo(self.username, self.password)
            self.person_info.prepare()
        except Exception as err:
            print(err)
            return

        if self.person_info.get_identification() is not None:
            print('登录成功!')
            self.person_info.set_priority(self.priority)
            print('区有优先级加载成功!')
            if not status:
                print('跳至set_priority命令开始设置区域优先级!')
                self.do_set_priority('')
        else:
            print('登录失败!')

    def do_set_priority(self, arg):
        """设置区域优先级:
    根据sequence number来设置,序号在前代表优先级越高,预约时会先从优先级高的区域开始预约.
    可以请使用tips命令再次查看区域信息.
        """
        if self.person_info is None:
            print('请先登录后再来设置区域优先级!')
            return

        print('开始设置区域优先级:')
        self.do_tip('')
        print('\t请根据sequence number来设置,序号在前代表优先级越高,预约时会先从优先级高的区域开始预约.')
        print('\t请一次输入你的优先级队列,以空格间隔开.不符合要求的无法录入配置.')

        priority = input('Enter priority queue:')
        for val in priority.split(' '):
            self.priority.append(self.record[val])

        self.person_info.set_priority(self.priority)

    def do_tip(self, arg):
        """显示不同座位区域的代号信息
        """
        print('以下是对应的区域信息:')
        count = 0
        for key, value in REFLECT_NAME.items():
            count += 1
            print(f'\tthis is sequence number:{count}. {key} - {value}')
            if len(self.record) < len(REFLECT_NAME):
                self.record[str(count)] = key
        print()

    def do_show(self, arg):
        """信息查询:
    -self 个人预约信息,无需其他参数.
        ex: show -self
    -free 区域空闲时间,指定空闲时间长度和区域的sequence number来进行查看.
        ex: show -free 30 4
        ex: show -free 100 2 3 4
    注意:
        二者功能不能兼容,self的优先级高于free.
        当指定查看多个区域的空闲时间时,终端可能打印过长,请仔细斟酌后确定要查看的区域.
        -free 后的第一个参数是空闲时间长度,单位为分钟;之后的为区域的sequence number.

        需要先登录才能使用该功能,使用check命令登录.
        可以使用tip命令查看区域的sequence number.
        """
        if self.person_info is None:
            print('请先登录后再来查看信息!')
            return

        is_self = False
        start_append = False
        args: list[str] = []

        for index, i in enumerate(str(arg).split(' ')):
            if i == '-self' and index == 0:
                is_self = True
                break
            elif i == '-free' and index == 0:
                start_append = True
                continue

            if start_append:
                if i.isdigit():
                    args.append(i)
                else:
                    print('参数错误!free后参数中不能有数字外的值!!')
                    return

        if not is_self and len(args) < 2:
            print("请确保你输入的参数正确!")
            return
        data = list(map(lambda x: self.record[x], args[1:]))

        try:
            if is_self:
                self.person_info.show_reservation()
            elif start_append:
                construction_info = get_construction_info(self.person_info.get_identification())
                construction_info.show_area_with_spare(*data, gap=int(args[0]), show=True)
        except Exception as err:
            print(err)
            return

    def do_cancel(self, arg):
        """取消个人预约:
    -id 使用show -self查看预约的id
        """
        if self.person_info is None:
            print('请先登录后再来取消预约!')
            return

        self.do_show('-self')

        args = str(arg).split(' ')
        if args[0] != '-id':
            print('请输入正确的参数!')
            return

        try:
            self.person_info.cancel_reservation(args[1])
        except Exception as err:
            print(err)
            return

    def do_make(self, arg):
        """进行预约:
    -start 预约的起始时间 hh:mm
    -end   预约的终止时间 hh:mm
    ex: make -start 09:00 -end 19:00

    会根据配置的区域优先级进行座位的筛选.
        """
        if self.person_info is None:
            print('请先登录后再来进行预约!')
            return
        args = str(arg).split()
        if len(args) != 4:
            print('请输入正确的参数!')
            return

        start, end = '', ''
        for key, val in enumerate(args):
            if val == '-start':
                start = args[key + 1]
            if val == '-end':
                end = args[key + 1]
        if start == '' or end == '':
            print('请输入正确的参数!')
            return

        try:
            data = self.person_info.find_seat(start, end)
            if len(data['not_successful']) == 0 and data['duration'] != '':
                print('已为您找到合适的位置:')
                print(
                    f"\t{data['room_name']}:{data['seat']}; from {data['duration'][0]} to {data['duration'][1]} is spare.")
                print('开始预约...')
                print(f'起始时间为:{start},终止时间为:{end}.')
                self.person_info.make_reservation(start, end, data['dev_id'])
            else:
                print('暂未找到合适的位置,最大限度满足您的时间需求:')
                for key, i in enumerate(data['not_successful']):
                    print(
                        f"\tsequence number:{key + 1} - {i['room_name']}:{i['seat']}; from {i['duration'][0]} to {i['duration'][1]} is spare.")
                ok = True
                while ok:
                    ok = True
                    index = int(input('请选择您觉得最合适的位置(sequence number):'))
                    if index > len(data['not_successful']) or index <= 0:
                        print('请输入正确的sequence number!')
                        ok = False
                print('开始预约...')
                print(
                    f"起始时间为:{data['not_successful'][index - 1]['duration'][0]},终止时间为:{data['not_successful'][index - 1]['duration'][1]}.")
                self.person_info.make_reservation(data['not_successful'][index - 1]['duration'][0],
                                                  data['not_successful'][index - 1]['duration'][1])
        except Exception as err:
            print(err)
            return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    cli = MyCLI()
    cli.cmdloop()
